"""Read-only verifier for the Omega Situation Room public evaluation candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUALIFIED_CANDIDATE_ID = "OMEGA_SITUATION_ROOM_QUALIFIED_PUBLIC_EVALUATION_CANDIDATE"
QUALIFIED_CANDIDATE_STATUS = "QUALIFIED_PUBLIC_EVALUATION_CANDIDATE"
PUBLIC_MICROSITE_STATUS = "ACTIVE"
PUBLIC_MICROSITE_URL = "https://omega.midex.app/"
CANONICAL_PUBLIC_MICROSITE_STATUS = "ACTIVE"
CANONICAL_PUBLIC_MICROSITE_URL = "https://omega.midex.app/"
VERCEL_PROJECT_URL = "https://omega-situation-room.vercel.app/"
QUALIFIED_PREVIEW_STATUS = "ACTIVE"
PREVIEW_DEPLOYMENT_STATUS = "ACTIVE"
CUSTOM_DOMAIN_STATUS = "ATTACHED_AND_QUALIFIED"
CHINATALK_SUBMISSION_STATUS = "NOT_SUBMITTED / SUBMISSION_WINDOW_CLOSED"
PUBLIC_REPOSITORY = "https://github.com/kevinadriancervantes/omega-situation-room"
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
    for label, document in (("allowlist", allow), ("manifest", manifest), ("privacy receipt", privacy)):
        if document.get("candidate_id") != QUALIFIED_CANDIDATE_ID:
            fail(errors, f"{label} candidate ID is not {QUALIFIED_CANDIDATE_ID}")
    if allow.get("status") != QUALIFIED_CANDIDATE_STATUS:
        fail(errors, "allowlist status is not QUALIFIED_PUBLIC_EVALUATION_CANDIDATE")
    if manifest.get("classification") != QUALIFIED_CANDIDATE_STATUS:
        fail(errors, "manifest classification is not QUALIFIED_PUBLIC_EVALUATION_CANDIDATE")
    if seal.get("classification") != QUALIFIED_CANDIDATE_STATUS:
        fail(errors, "seal classification is not QUALIFIED_PUBLIC_EVALUATION_CANDIDATE")
    manifest_status = manifest.get("status", {})
    expected_public_status = {
        "public_microsite_status": PUBLIC_MICROSITE_STATUS,
        "public_microsite_url": PUBLIC_MICROSITE_URL,
        "canonical_public_microsite_status": CANONICAL_PUBLIC_MICROSITE_STATUS,
        "canonical_public_microsite_url": CANONICAL_PUBLIC_MICROSITE_URL,
        "vercel_project_url": VERCEL_PROJECT_URL,
        "qualified_preview_status": QUALIFIED_PREVIEW_STATUS,
        "preview_deployment_status": PREVIEW_DEPLOYMENT_STATUS,
        "custom_domain_status": CUSTOM_DOMAIN_STATUS,
        "chinatalk_submission_status": CHINATALK_SUBMISSION_STATUS,
    }
    for key, expected in expected_public_status.items():
        if manifest_status.get(key) != expected:
            fail(errors, f"manifest {key} is not {expected}")
    for key in ("deployment_status", "production_microsite_status", "submission_status", "microsite_target"):
        if key in manifest_status:
            fail(errors, f"manifest retains obsolete or ambiguous {key}")
    for label, document in (("seal", seal), ("privacy receipt", privacy)):
        for key, expected in expected_public_status.items():
            if document.get(key) != expected:
                fail(errors, f"{label} {key} is not {expected}")
        for key in ("deployment_status", "production_microsite_status", "submission_status", "microsite_target"):
            if key in document:
                fail(errors, f"{label} retains obsolete or ambiguous {key}")
    if privacy.get("status") != "PASS" or privacy.get("violations") != []:
        fail(errors, "privacy receipt is not a clean PASS")
    privacy_requirements = {
        "raw_runtime_evidence_included": False,
        "raw_model_or_provider_responses_included": False,
        "credentials_or_authentication_material_included": False,
        "machine_local_identity_included": False,
        "proprietary_game_assets_included": False,
        "private_git_history_included": False,
    }
    for key, expected in privacy_requirements.items():
        if privacy.get(key) is not expected:
            fail(errors, f"privacy receipt is not false for {key}")

    # CFF 1.2.0 semantic checks that do not require installing a parser.
    if not re.search(r"(?m)^cff-version:\s*1\.2\.0\s*$", cff):
        fail(errors, "CFF version is not 1.2.0")
    for field in ("title:", "message:", "type: software", "authors:", "version:", "license: MIT", "repository-code:", "references:"):
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
        fail(errors, "CFF date-released is forbidden before an authorized release")
    repository_match = re.search(r"(?m)^repository-code:\s*[\"']?([^\"'\s]+)[\"']?\s*$", cff)
    if not repository_match or repository_match.group(1) != PUBLIC_REPOSITORY:
        fail(errors, "CFF repository-code is not the qualified contest repository")
    if not re.search(r"(?im)^\s*url:\s*[\"']?https://omega\.midex\.app/[\"']?\s*$", cff):
        fail(errors, "CFF canonical URL is not https://omega.midex.app/")
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

    # Read local Git metadata without exposing addresses. The qualified
    # contest candidate must contain only GitHub noreply identities.
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
            if non_public_identity:
                fail(errors, "non-public Git identity detected in qualified contest history")
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
    email_address = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
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
        for address in email_address.findall(text):
            if not address.lower().endswith("@users.noreply.github.com"):
                fail(errors, f"private email address detected in {path_text}")
        for match in ipv4.findall(text):
            if not match.startswith("127.") and match not in {"0.0.0.0", "255.255.255.255"}:
                fail(errors, f"non-loopback IP-like value detected in {path_text}")
                break
        for marker in marker_fragments:
            if marker.lower() in text.lower():
                fail(errors, f"private path marker detected in {path_text}: {marker}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    site = (ROOT / "site/index.html").read_text(encoding="utf-8")
    readme_status_text = readme.upper()
    site_status_text = site.upper()
    if "QUALIFIED PUBLIC EVALUATION CANDIDATE" not in readme or "QUALIFIED PUBLIC EVALUATION CANDIDATE" not in site:
        fail(errors, "qualified public evaluation candidate status is missing from README and/or site")
    for stale in ("OMEGA_SITUATION_ROOM_LOCAL_QUALIFIED_CANDIDATE", "LOCAL_QUALIFIED_CANDIDATE", "LOCAL CANDIDATE"):
        if stale in readme or stale in site:
            fail(errors, f"stale current-state candidate marker remains in README or site: {stale}")
    for marker in (
        "PROVEN_TODAY",
        "IMPLEMENTED_OR_UNDER_QUALIFICATION",
        "PROPOSED_CONTEST_EXPERIMENT",
        "NOT_SUBMITTED",
        "CANDIDATE_CLASSIFICATION",
        "PUBLIC_MICROSITE_STATUS",
        "PUBLIC_MICROSITE_URL",
        "CANONICAL_PUBLIC_MICROSITE_STATUS",
        "CANONICAL_PUBLIC_MICROSITE_URL",
        "VERCEL_PROJECT_URL",
        "QUALIFIED_PREVIEW_STATUS",
        "PREVIEW_DEPLOYMENT_STATUS",
        "CUSTOM_DOMAIN_STATUS",
        "ATTACHED_AND_QUALIFIED",
        "SUBMISSION_WINDOW_CLOSED",
    ):
        if marker not in readme_status_text or marker not in site_status_text:
            fail(errors, f"status marker missing from README and/or site: {marker}")
    for url in (CANONICAL_PUBLIC_MICROSITE_URL, VERCEL_PROJECT_URL):
        if url not in readme or url not in site:
            fail(errors, f"public URL missing from README and/or site: {url}")
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

    public_history = manifest.get("public_history", {})
    expected_history = {
        "repository": PUBLIC_REPOSITORY,
        "current_history_status": "PUBLIC_SAFE_NOREPLY_HISTORY",
        "projection_method": "FRESH_ONE_COMMIT_PROJECTION_FROM_PHASE_2R_QUALIFIED_TREE",
        "initial_public_safe_commit": "c65f68d5a04c11fd7a135b3a6e8dfb07ba791298",
        "public_identity_status": "HUMAN_CONFIRMED_GITHUB_NOREPLY",
    }
    for key, expected in expected_history.items():
        if public_history.get(key) != expected:
            fail(errors, f"public history metadata mismatch: {key}")

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
    print("public_microsite_status=ACTIVE")
    print(f"public_microsite_url={PUBLIC_MICROSITE_URL}")
    print("qualified_preview_status=ACTIVE")
    print("preview_deployment_status=ACTIVE")
    print(f"custom_domain_status={CUSTOM_DOMAIN_STATUS}")
    print("chinatalk_submission_status=NOT_SUBMITTED / SUBMISSION_WINDOW_CLOSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
