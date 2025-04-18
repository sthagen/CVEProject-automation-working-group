*The goal of this document is to create a proposal for an archiving solution of references linked in published CVE records.*

**Why?**

- [CVE Reference Investigations](https://docs.google.com/presentation/d/1jO7y1WHAUTWZwUl4tP3ZRJT0gvG6KxQklUvsXoM6NF4/edit#slide=id.g2793d2f3e58_2_50)
  - Link rot (30% of CVE records have at least one dead link)
  - Potential for malicious takeover of invalid domains referenced in CVE records
  - Reliance on archive.org for archival

**High-level requirements discussion:**

- Is there a subset of references that we want to archive, or should this effort cover all references?
  - AWG (Dec 3,2024): there is no distinction between references to determine which should vs shouldn't be archived; we should archive them all
- Do we want to archive references in ADP records as well?
  - AWG (Dec 3,2024): we should archive ADP references too (especially secretariat's container that contains primary references)
- How often should references be re-archived beyond the first archival?
  - AWG (Dec 3,2024): we should re-archive at intervals; 0, 3, 10, 90?
  - Do we need to store older versions? How many?
    - AWG (Dec 3,2024): three latest versions? Build with the expectation of having multiple versions; MVP is having one archived reference. The goal is to always have at least one archived reference to prevent dead links. If we're snapshotting multiple times, we should keep previous versions.
- How fast do we need to archive a reference once it appears in a record?
  - AWG (Dec 3,2024): at submission, ideally
- Do we need to archive a full page, or just the text of a page?
  - If the full page, does it need to store all of the assets of the pages (HTML/JS/CSS) so that it can be rendered on its own once archived?
  - AWG (Dec 3,2024): multiple formats if possible: preferably one user-acessible format (image/pdf via headless browser) and one machine-readable (HTML/WARC)
- How should the references be retrievable?
  - Do we need a viewer of the archived references, or just provide them in their raw form and allow users to download them?
  - AWG (Dec 3,2024): user story: I have an existing (dead) URL, show me the archived version of it.
  - AWG (Dec 3,2024): user story: I have a CVE ID, show me all of its archived references.
  - AWG (Dec 3,2024): no need for generic search of all references

**Architectural Approaches**

- Ready-made solutions:
  - [Archivebox](https://archivebox.io/)
    - Self-hosted solution with a myriad of capture formats and storage options
    - Some notes on running ArchiveBox from Tod: https://github.com/todb/junkdrawer/tree/main/cve-kev-refs
    - The service itself does not have to be exposed to the Internet, we only want its scraping and archiving capabilities; retrieval could be direct from storage (e.g. S3 bucket or web server front-end)
    - cost: storage + maintenance/dev effort
      - deploy archivebox: VM (EC2) + S3 + auth + logging
      - required CVE Services dev work: notify archiving service/job to create a snapshot on CVE publish
      - long-term maintenance

- Third-party solutions:
  - Relying on archive.org
    - rumor: as part CVE data ingestion, Qualys already submits every CVE reference to archive.org
  - Library of Congress
    - how can we contact the Web Archive team?

- Home-grown solutions:
  - Simple: CI + git + wget
  - More advanced: Cron jobs + object storage + metadata DB + scraper
  - Purpose-built scrapers:
    - https://github.com/Rhizome-Conifer/conifer
    - https://github.com/internetarchive/brozzler
    - https://webcuratortool.readthedocs.io/en/latest/guides/user-manual.html
    - https://github.com/gildas-lormeau/SingleFile
    - custom Python stack: playwrigth + warcio (or similar)
  - home-grown solutions quickly hit limits that may be solved in ArchiveBox; page timeouts, retries, inaccessible pages, etc.
  - cost:
    - initial dev work + deployment
      - architecture could be similar to cvelist bulk download repo
    - CVE Services dev work (same as archivebox)
    - long-term maintenance plus improvements

 - Paid solutions:
   - https://perma.cc/
     - no public pricing available (found $0.25 per link)
   - https://www.pagefreezer.com/
     - no public pricing available, focused on compliance with recordkeeping requirements (might be pricey??)
   - https://urlbox.com/pricing
     - takes screenshots of pages

**Cost & Resource Analysis**

- ArchiveBox:
  - Self-managed:
    - Storage costs (S3):
      - average webpage archive (HTML, screenshots, resources): ~10MB
      - 500k sites * 10MB = ~5TB storage (this feels really large...)
      - ~$115/month for 5TB
    - Compute costs ECS:
      - 1 vCPU, 2GB RAM
      - ~$35/month
    - Serving content from S3 CloudFront:
      - 1M requests / 1TB transfer
      - ~$88/month
    - Rough total: $238/month
  - Hosted solutions:
    - Complete list at https://github.com/ArchiveBox/ArchiveBox?tab=readme-ov-file#-other-options
    - Fully-managed: https://elest.io/open-source/archivebox
      - XL: $164/month (may need more storage)
    - AWS marketplace: https://aws.amazon.com/marketplace/pp/prodview-hwqaitd4t3vzy
      - t3.large compute: $163/month
      - storage 500GB: $50/month
      - most likely need to include CloudFront cost to serve content

- Github-based solution:
  - A hybrid GitHub-based solution that relies on NPM libraries to scrape web content instead of ArchiveBox and
    store the content in either a GitHub repository (looking at repository size limitations) or external storage (likely S3 bucket) would require less cost (possibly no cost or only paying for storage and
    serving of the content), but requires more development time up front.
  - Details in [PowerPoint slides](https://github.com/CVEProject/automation-working-group/blob/master/meeting-notes/files/2025-01-14%20CVE%20Reference%20Archiver%20Proposal.pptx) (requires download of slides)

**Questions & Discussion**

_Dec 3, 2024_:
- Do we replace dead links with their archived versions?
  - AWG: leave the original link and indicate that it may be invalid and provide a way to resolve it to its archived version
- Should a CVE record instead be improved to contain enough information to not heavily depend on references?
  - AWG: it may be impractical to house all data that is currently placed in referenced content in the CVE record itself
  - AWG: are there common data patterns that appear in references but not in CVE record? CVE record often contains summarized versions of metadata about the vulnerability.
- Are there legal considerations for serving archived content?
  - AWG: Kris to double-check with Alec
- Should archived content be limited to CNAs to prevent bulk download by the public?
  - AWG: bulk download of all archived content could be added in a later version, not in MVP
  - AWG: estimated based on local experiments 3TB of archived data for the entired CVE data set

_Dec 17, 2024_:
- 593,848 unique references as of 2024-12-06
- Paid solutions seem to expensive and there would like not be budget for them
- Relying on archive.org is not an optimal solution because it could be shut down at any time and we'd lose the entire data set
- Library of Congress is difficult to contact and would most likely take a while to take this on
- We need to create a cost estimate for deploy+maintain of ArchiveBox, and create+deploy+maintain of a simple CI-driven solution

**AWG-recommended Solution**

Through discussion of the various requirements, it was determined that both managed (paid), self-hosted solutions
(on AWS infrastructure), and self-developed options are viable solutions to the archival of CVE references. The cost
of either solution is within reason, and it is thus up to the assigned developer(s) to decide which approach is most
flexible and effective to achieve the result.

The AWG recommends the allocation of developer resources to further refine the proposed implementation, and create
an MVP that:
- Is able to archive the content provided by a given reference included in a CVE record
- Saves the scraped content in one human-readable format (png, pdf) and one machine-readable format (html/jss/css, warc)
- Gives a user the ability to easily retrieve an archived reference
- Generates an archived version of a reference at four intervals: 0, 3, 10, 90 days
