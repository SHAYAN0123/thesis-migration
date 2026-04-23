# EU Cloud Sovereignty Framework — 7 Themes
# Derived from pre-thesis: comparative analysis of 6 EU frameworks
# (EU SEAL, CIGREF, Gaia-X, Dutch BIO, German Souveräner Cloud, French SecNumCloud)
# 
# Use these themes to evaluate whether P_n+1 is sovereignty-compliant.

## Theme 1: Jurisdiction
- System must not depend on services governed by non-EU law
- No exposure to extraterritorial legislation (e.g., US CLOUD Act)
- Check: does the code call APIs operated by non-EU entities?

## Theme 2: Data Localisation
- Data must be storable within EU borders
- No hard-coded regions outside EU
- Check: can the system run with data entirely in the EU?

## Theme 3: Operational Autonomy
- System must be operable without depending on a single vendor
- No vendor-specific control plane required
- Check: can the system run independently of any cloud provider?

## Theme 4: Lock-in Avoidance
- No vendor-specific APIs in the application code
- No proprietary data formats that prevent migration
- Check: does the code import any vendor SDK (boto3, google-cloud, azure-sdk)?

## Theme 5: Supply-Chain Control
- No single vendor controls the entire stack
- Dependencies should be replaceable
- Check: is there a single point of vendor failure?

## Theme 6: Openness & Standards
- System should use open standards and protocols (HTTP, SQL, AMQP, S3-compatible APIs)
- Prefer open-source over proprietary
- Check: are the interfaces based on open standards?

## Theme 7: Sustainability
- System should be maintainable and portable long-term
- Not tied to a service that could be deprecated
- Check: can the system be maintained without vendor cooperation?

---

## How to Use This for Verification

For each file in P_n+1 (new-system), check:
- Does it import any cloud-specific SDK? → Violates Theme 4
- Does it hardcode a cloud provider region? → Violates Theme 2
- Does it call a proprietary API? → Violates Themes 1, 3, 6
- Is there a single vendor dependency? → Violates Theme 5
- Could this code run on any infrastructure? → If yes, Themes 3, 7 satisfied