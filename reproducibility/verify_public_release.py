"""Read-only verifier for the Omega Situation Room local candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = ROOT / "governance" / "public-release-allowlist.json"
MANIFEST = ROOT / "governance" / "release-manifest.json"
SEAL = ROOT / "governance" / "release-seal.json"
PRIVACY = ROOT / "governance" / "privacy-receipt.json"
CLAIMS = ROOT / "governance" / "CLAIMS.md"
CFF = ROOT / "CITATION.cff"
CLAIM_MAP = ROOT / "governance" / "claim-surface-map.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def relative_files() -> tuple[set[str], list[str]]:
    files: set[str] = set()
    errors: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            errors.append(f"symlink is not allowed: {path.relative_to(ROOT)}")
            continue
        if path.is_file():
            files.add(path.relative_to(ROOT).as_posix())
    return files, errors


def main() -> int:
    errors: list[str] = []
    for required in (ALLOWLIST, MANIFEST, SEAL, PRIVACY, CLAIMS, CFF, CLAIM_MAP):
        if not required.is_file():
            fail(errors, f"required file missing: {required.relative_to(ROOT)}")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    allow = read_json(ALLOWLIST)
    manifest = read_json(MANIFEST)
    seal = read_json(SEAL)
    privacy = read_json(PRIVACY)
    claims = CLAIMS.read_text(encoding="utf-8")
    cff = CFF.read_text(encoding="utf-8")
    claim_map = read_json(CLAIM_MAP)

    allowed = set(allow.get("paths", []))
    physical, tree_errors = relative_files()
    errors.extend(tree_errors)
    if physical != allowed:
        fail(errors, f"allowlist mismatch; unexpected={sorted(physical - allowed)}, missing={sorted(allowed - physical)}")

    required_paths = {
        "README.md",
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "CITATION.cff",
        "governance/CLAIMS.md",
        "governance/privacy-policy.md",
        "governance/privacy-receipt.json",
        "governance/public-release-allowlist.json",
        "governance/release-manifest.json",
        "governance/release-seal.json",
        "protocol/EVAL_SPEC.md",
        "protocol/METRICS.md",
        "protocol/ADJUDICATION.md",
        "protocol/EXPERIMENT_DESIGN.md",
        "protocol/LIMITATIONS.md",
        "evidence/README.md",
        "evidence/STATUS_MATRIX.json",
        "evidence/IMPLEMENTATION_QUALIFICATION_SUMMARY.json",
        "evidence/fixtures/contract-fixture.json",
        "reproducibility/README.md",
        "reproducibility/verify_public_release.py",
        "site/index.html",
        "site/styles.css",
        "site/app.js",
    }
    if required_paths - physical:
        fail(errors, f"required paths missing: {sorted(required_paths - physical)}")

    forbidden_suffixes = (".env", ".pem", ".key", ".p12", ".sqlite", ".db", ".exe", ".dll", ".bin")
    for path_text in sorted(physical):
        path = ROOT / Path(path_text)
        if path.name.startswith(".env") or path.suffix.lower() in forbidden_suffixes:
            fail(errors, f"forbidden filename or extension: {path_text}")

    payload_paths = sorted(allowed - {"governance/release-manifest.json", "governance/release-seal.json"})
    entries = manifest.get("payload_files", [])
    entry_map = {entry.get("path"): entry for entry in entries}
    if set(entry_map) != set(payload_paths):
        fail(errors, "manifest payload paths do not equal allowlisted payload paths")
    for path_text in payload_paths:
        path = ROOT / Path(path_text)
        entry = entry_map.get(path_text, {})
        actual = file_sha256(path)
        if entry.get("sha256") != actual:
            fail(errors, f"payload hash mismatch: {path_text}")
        if entry.get("classification") not in {"GENERATED", "COPIED_VERBATIM", "DERIVED"}:
            fail(errors, f"invalid artifact classification: {path_text}")

    tree_digest = hashlib.sha256()
    for path_text in payload_paths:
        tree_digest.update(path_text.encode("utf-8"))
        tree_digest.update(b"\0")
        tree_digest.update(file_sha256(ROOT / Path(path_text)).encode("ascii"))
        tree_digest.update(b"\n")
    if manifest.get("payload_tree_sha256") != tree_digest.hexdigest():
        fail(errors, "payload tree hash mismatch")

    manifest_hash = file_sha256(MANIFEST)
    if seal.get("manifest_sha256") != manifest_hash:
        fail(errors, "release seal does not bind the release manifest")
    if manifest.get("classification") != "LOCAL_QUALIFIED_CANDIDATE":
        fail(errors, "manifest classification is not LOCAL_QUALIFIED_CANDIDATE")
    if seal.get("classification") != "LOCAL_QUALIFIED_CANDIDATE":
        fail(errors, "seal classification is not LOCAL_QUALIFIED_CANDIDATE")
    if manifest.get("status", {}).get("submission_status") != "NOT_SUBMITTED":
        fail(errors, "manifest submission status is not NOT_SUBMITTED")
    if manifest.get("status", {}).get("deployment_status") != "NOT_DEPLOYED":
        fail(errors, "manifest deployment status is not NOT_DEPLOYED")
    if seal.get("submission_status") != "NOT_SUBMITTED" or seal.get("deployment_status") != "NOT_DEPLOYED":
        fail(errors, "seal status is not NOT_SUBMITTED / NOT_DEPLOYED")
    if privacy.get("status") != "PASS" or privacy.get("violations") != []:
        fail(errors, "privacy receipt is not a clean PASS")

    # CFF 1.2.0 semantic checks that do not require installing a parser.
    if not re.search(r"(?m)^cff-version:\s*1\.2\.0\s*$", cff):
        fail(errors, "CFF version is not 1.2.0")
    for field in ("title:", "message:", "type: software", "authors:", "version:", "license: MIT", "references:"):
        if field not in cff:
            fail(errors, f"CFF required field missing: {field}")
    root_keys = re.findall(r"(?m)^([A-Za-z][A-Za-z0-9-]*):", cff)
    if len(root_keys) != len(set(root_keys)):
        fail(errors, "CFF contains duplicate top-level keys")
    if re.search(r"(?m)^\s+role\s*:", cff):
        fail(errors, "CFF contains unsupported person-object role metadata")
    author_block_match = re.search(r"(?ms)^authors:\s*\n(.*?)(?=^version:)", cff)
    author_block = author_block_match.group(1) if author_block_match else ""
    if not re.search(r"(?m)^\s+- family-names:\s*Cervantes\s*$", author_block):
        fail(errors, "CFF root author is not Kevin Cervantes")
    if not re.search(r"(?m)^\s+given-names:\s*Kevin\s*$", author_block):
        fail(errors, "CFF root author given name is not Kevin")
    if "Wilkinson" in author_block:
        fail(errors, "CFF incorrectly lists Liam Wilkinson as an Omega root author")
    reference_block = cff[cff.find("references:"):] if "references:" in cff else ""
    for marker in ("civ6-mcp", "Wilkinson", "https://github.com/lmwilki/civ6-mcp"):
        if marker not in reference_block:
            fail(errors, f"CFF upstream reference marker missing: {marker}")
    if re.search(r"(?m)^date-released:", cff):
        fail(errors, "CFF date-released is forbidden for an unreleased local candidate")
    if re.search(r"(?m)^repository-code:", cff):
        fail(errors, "CFF repository-code must be deferred until a candidate repository exists")
    if re.search(r"(?im)^\s*url:\s*https://omega\.midex\.app\s*$", cff):
        fail(errors, "CFF represents the undeployed omega.midex.app as an existing URL")
    if re.search(r"(?i)(TBD|REPLACE_ME|example\.com)", cff):
        fail(errors, "CFF contains a future or placeholder value")

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    notices_text = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    for marker in ("Omega Situation Room original material", "Kevin Adrian Cervantes", "MIT License"):
        if marker not in license_text:
            fail(errors, f"root license marker missing: {marker}")
    for marker in ("civ6-mcp", "Liam Wilkinson", "MIT License", "Permission is hereby granted"):
        if marker not in notices_text:
            fail(errors, f"upstream license/provenance marker missing: {marker}")

    # Machine-readable claim reconciliation: every material claim has one
    # ledger entry, explicit asserted surfaces, and supporting evidence.
    expected_claims = ("PT-001", "PT-002", "PT-003", "IQ-001", "IQ-002", "PE-001", "PE-002")
    if claim_map.get("authoritative_ledger") != "governance/CLAIMS.md":
        fail(errors, "claim map authoritative ledger is incorrect")
    claim_rows = claim_map.get("claims", [])
    mapped_ids = [row.get("id") for row in claim_rows if isinstance(row, dict)]
    if sorted(mapped_ids) != sorted(expected_claims) or len(mapped_ids) != len(set(mapped_ids)):
        fail(errors, "claim map does not contain exactly the expected claim IDs")
    for row in claim_rows:
        if not isinstance(row, dict):
            fail(errors, "claim map contains a non-object entry")
            continue
        claim_id = row.get("id")
        if row.get("ledger_entry") != claim_id:
            fail(errors, f"claim map ledger entry mismatch: {claim_id}")
        if f"| {claim_id} |" not in claims:
            fail(errors, f"claim map ID is absent from the authoritative ledger: {claim_id}")
        surfaces = row.get("asserted_surfaces", [])
        if not isinstance(surfaces, list) or not surfaces:
            fail(errors, f"claim map has no asserted surfaces: {claim_id}")
            surfaces = []
        for surface in surfaces:
            if surface not in physical:
                fail(errors, f"claim surface is not a candidate file: {claim_id} / {surface}")
            elif claim_id not in (ROOT / Path(surface)).read_text(encoding="utf-8"):
                fail(errors, f"claim ID absent from asserted surface: {claim_id} / {surface}")
        evidence = row.get("supporting_evidence", [])
        if not isinstance(evidence, list) or not evidence:
            fail(errors, f"claim map has no supporting evidence: {claim_id}")
        for item in evidence if isinstance(evidence, list) else []:
            if isinstance(item, str) and not item.startswith(("http://", "https://")) and item not in physical:
                fail(errors, f"claim supporting evidence is not a candidate file or URL: {claim_id} / {item}")

    # Read local Git metadata without exposing addresses. A non-public local
    # history is acceptable only when the manifest explicitly requires a
    # fresh public projection before any remote publication.
    git_history_result = "NOT_CHECKED"
    if (ROOT / ".git").exists():
        git_result = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--format=%H%x00%ae%x00%ce"],
            capture_output=True,
            text=True,
            check=False,
        )
        if git_result.returncode != 0:
            fail(errors, "local Git-history metadata could not be inspected")
        else:
            non_public_identity = False
            for record in git_result.stdout.splitlines():
                fields = record.split("\0")
                for email in fields[1:3]:
                    if email and not email.lower().endswith("@users.noreply.github.com"):
                        non_public_identity = True
            policy = manifest.get("public_history", {})
            if non_public_identity:
                if (
                    policy.get("current_local_history") != "NOT_PUBLIC_SAFE"
                    or policy.get("recommended_projection") != "FRESH_ONE_COMMIT_PUBLIC_PROJECTION"
                    or policy.get("public_identity") != "HUMAN_APPROVED_GITHUB_NOREPLY_REQUIRED"
                ):
                    fail(errors, "non-public Git identity requires an explicit fresh public-history policy")
                else:
                    git_history_result = "PASS_FRESH_PUBLIC_PROJECTION_REQUIRED"
            else:
                git_history_result = "PASS_PUBLIC_NOREPLY_IDENTITIES"

    # The verifier's own source contains audit vocabulary by design; all other
    # candidate files are checked for values and filesystem-like disclosures.
    scan_files = sorted(physical - {"reproducibility/verify_public_release.py"})
    drive_path = re.compile(r"\b[A-Za-z]:[\\/][^\r\n]+")
    unix_home = re.compile(r"/(?:Users|home|private|var)/", re.IGNORECASE)
    secret_assignment = re.compile(
        r"\b(?:api|access|client|service|secret)[-_]?(?:key|token|secret)\s*[:=]\s*[^\s`]+",
        re.IGNORECASE,
    )
    bearer = re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}", re.IGNORECASE)
    cookie = re.compile(r"\bCookie\s*:\s*\S+", re.IGNORECASE)
    private_key = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
    ipv4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    mac = re.compile(r"\b[0-9A-F]{2}(?::[0-9A-F]{2}){5}\b", re.IGNORECASE)
    marker_fragments = ("private" + "-archive", "." + "work", "omega" + "_lab")
    for path_text in scan_files:
        text = (ROOT / Path(path_text)).read_text(encoding="utf-8")
        checks = (
            (drive_path, "absolute Windows path"),
            (unix_home, "absolute Unix home/private path"),
            (secret_assignment, "secret-like assignment"),
            (bearer, "authorization value"),
            (cookie, "cookie material"),
            (private_key, "private key marker"),
            (mac, "MAC address"),
        )
        for pattern, label in checks:
            if pattern.search(text):
                fail(errors, f"{label} detected in {path_text}")
        for match in ipv4.findall(text):
            if not match.startswith("127.") and match not in {"0.0.0.0", "255.255.255.255"}:
                fail(errors, f"non-loopback IP-like value detected in {path_text}")
                break
        for marker in marker_fragments:
            if marker.lower() in text.lower():
                fail(errors, f"private path marker detected in {path_text}: {marker}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    site = (ROOT / "site/index.html").read_text(encoding="utf-8")
    for marker in (
        "PROVEN_TODAY",
        "IMPLEMENTED_OR_UNDER_QUALIFICATION",
        "PROPOSED_CONTEST_EXPERIMENT",
        "NOT_SUBMITTED",
        "NOT_DEPLOYED",
    ):
        if marker not in readme or marker not in site:
            fail(errors, f"status marker missing from README and/or site: {marker}")
    for claim_id in ("PT-001", "PT-002", "PT-003", "IQ-001", "IQ-002", "PE-001", "PE-002"):
        if claim_id not in claims or claim_id not in readme or claim_id not in site:
            fail(errors, f"claim ID not reconciled across ledger, README, and site: {claim_id}")
    if "MIT License" not in license_text:
        fail(errors, "MIT license text missing")
    for marker in ("Liam Wilkinson", "civ6-mcp", "CivBench"):
        if marker not in readme or marker not in site:
            fail(errors, f"provenance marker missing: {marker}")
    for marker in (
        'id="evaluation-question"',
        'id="governance-metrics"',
        'id="proposed-experiment"',
        'id="limitations"',
        'id="provenance"',
        'id="reproducibility"',
    ):
        if marker not in site:
            fail(errors, f"microsite section missing: {marker}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    print(f"candidate={manifest['candidate_id']}")
    print(f"payload_files={len(payload_paths)}")
    print(f"payload_tree_sha256={tree_digest.hexdigest()}")
    print(f"manifest_sha256={manifest_hash}")
    print(f"seal_sha256={file_sha256(SEAL)}")
    print(f"cff_validation=PASS_SEMANTIC_1.2.0")
    print(f"git_history_privacy={git_history_result}")
    print("claim_surface_reconciliation=PASS")
    print("submission_status=NOT_SUBMITTED")
    print("deployment_status=NOT_DEPLOYED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
