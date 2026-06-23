# Resume and Professional Profile Review

## What this reference is for

Audit and concretely improve resumes, LinkedIn profiles, GitHub profiles, portfolios, personal sites, bios, and project lists for a specific target. The goal is clearer fit and denser truthful proof—not cosmetic perfection.

## When the agent should read it

Read this in Resume/Profile Mode, during job-search materials work, or when the user says their experience is hard to explain or their public proof feels weak.

## Source links used

- CareerOneStop resumes: https://www.careeronestop.org/JobSearch/Resumes/resumes.aspx
- MIT ATS guidance: https://capd.mit.edu/resources/make-your-resume-ats-friendly/
- Berkeley resume and ATS guidance: https://career.berkeley.edu/prepare-for-success/resumes/
- Yale impactful resume bullets: https://ocs.yale.edu/resources/writing-impactful-resume-bullets/
- MIT career toolkit: https://capd.mit.edu/resources/career-toolkit-crafting-an-effective-resume/
- LinkedIn profile guidance: https://www.linkedin.com/help/linkedin/answer/a554351
- LinkedIn Featured section: https://www.linkedin.com/help/linkedin/answer/a550399/manage-featured-samples-of-your-work-on-your-linkedin-profile?lang=en
- GitHub profile guidance: https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile
- GitHub README guidance: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes

Accessed 2026-06-23.

## The concrete process

### 1. Establish the target and artifact purpose

Ask for or infer:

- Target role, level, industry, and geography
- A current job description or representative role requirements
- Which artifact is being reviewed
- Submission channel: ATS upload, direct email, referral, recruiter, portfolio link, public profile
- Any privacy or disclosure constraints

A resume cannot be meaningfully optimized for “all jobs.” When no posting exists, use a clearly labeled target-role hypothesis.

### 2. Preserve facts before rewriting

Extract a fact bank:

- Titles, organizations, dates, and employment type
- Projects and responsibilities
- Tools and methods actually used
- Scale, constraints, stakeholders, and complexity
- Results, feedback, and artifacts
- Education, certifications, and licenses

Mark uncertain facts with brackets. Never manufacture metrics, clients, titles, credentials, or outcomes. Ask the user to verify every rewrite that adds specificity.

### 3. Audit the resume in seven passes

Use `assets/resume-review-rubric.md`.

#### Pass A: Target clarity

Can a reader tell within seconds what role or capability the resume supports? Check headline or summary only when it earns its space.

#### Pass B: Requirement coverage

Map common target requirements to exact evidence:

| Requirement | Resume evidence | Strength | Gap or rewrite |
|---|---|---|---|

Distinguish missing skill from missing proof and missing wording.

#### Pass C: Proof density

Prefer bullets that show action, context, method, and result:

```text
[action] [what/problem] using [method/tool], resulting in [verified outcome or useful artifact]
```

Before:

> Responsible for customer support and documentation.

After, only when factual:

> Resolved customer setup issues across email and chat, then converted recurring questions into six troubleshooting guides used by the support team.

When exact numbers do not exist, use honest forms of evidence:

- Scope: number or type of stakeholders, systems, cases, pages, modules, events
- Speed: deadline, turnaround, frequency
- Quality: error reduction, review result, reliability, adoption
- Complexity: constraints, integrations, ambiguity, migration, accessibility
- Artifact: shipped demo, procedure, dataset, report, documentation, test suite
- Recognition: verified feedback, selected work, expanded responsibility

Do not add a number merely to make a bullet look quantified.

#### Pass D: Signal hierarchy

Put the strongest and most relevant evidence where it will be seen. Remove or compress content that crowds out target-relevant proof. Nontraditional experience is valid when accurately labeled and connected to the target.

#### Pass E: Language

Replace vague wording with specific actions. Remove unsupported adjectives such as “expert,” “dynamic,” or “results-driven.” Use role vocabulary naturally and truthfully.

#### Pass F: ATS readability

ATS products and employer configurations differ. Use robust basics rather than claiming a universal score:

- Follow the employer's file-type instructions.
- Use simple, readable structure and standard section headings.
- Avoid critical information in headers, footers, text boxes, graphics, and complex tables.
- Avoid columns when they produce uncertain reading order.
- Use conventional fonts and bullets.
- Include relevant full terms and abbreviations when useful and accurate.
- Test text extraction or save a plain-text copy to inspect missing or reordered content.
- Do not keyword-stuff or hide text.

A visually designed resume may still be useful for direct delivery in a design field; keep a separate parsing-safe version for online applications.

#### Pass G: Trust and usability

Check dates, links, spelling, tense, consistent formatting, contact information, filename, and whether every claim can be explained in an interview.

### 4. Review LinkedIn or another professional profile

Check:

- **Headline:** target value, role family, or credible specialization—not a pile of buzzwords.
- **About:** short positioning statement, proof, interests, and an appropriate next step.
- **Experience:** accurate relationship to organizations; include contract, volunteer, project, or self-employed labels where applicable.
- **Skills:** relevant, supported, and not inflated.
- **Featured/work samples:** strongest proof with enough context.
- **Location and work preferences:** aligned with the actual search while respecting privacy.
- **Consistency:** dates, titles, and claims agree with the resume.

Never advise the user to imply employment or affiliation that did not exist.

### 5. Review GitHub

Check the public visitor path:

1. Profile name, bio, links, and contact route
2. Profile README, when useful
3. Pinned repositories selected for the target
4. Each pinned repository's first-screen README
5. Live demo or screenshots when appropriate
6. Setup reliability, tests, license, and recent maintenance
7. Commit or contribution context without treating raw activity as proof of quality

A target-relevant repository README should usually explain:

- Problem and intended user
- What works now
- Demo or visual evidence
- Architecture, stack, or important decisions
- Setup and use
- Testing or validation
- Constraints, tradeoffs, and next steps
- The user's individual contribution for team projects

Do not expose secrets, client code, private data, or unsafe deployment details.

### 6. Review a portfolio or personal site

Prioritize case-study evidence over a gallery of unexplained links:

- Problem and audience
- Constraints
- User's role
- Process and decisions
- Artifact or demo
- Result and evidence
- What changed after feedback
- Honest limitations

The minimum viable portfolio artifact may be one strong case study rather than a full website.

### 7. Produce concrete rewrites

For each priority issue, provide:

- Original text
- Revised text
- Why the change helps
- Facts the user must confirm

Do not rewrite the entire artifact before agreeing on the target and fact bank unless the user explicitly asks for a full rewrite.

### 8. Prioritize fixes

Use this order unless evidence suggests otherwise:

1. Factual or trust problem
2. Wrong target or weak positioning
3. Missing high-value proof
4. Weak bullets or case studies
5. ATS/readability failure
6. Broken links or incomplete public artifacts
7. Cosmetic polish

## Resume/Profile Mode output

```markdown
# Target alignment
[Target and evidence base]

## Strengths
[Specific strengths]

## Weaknesses and missing proof
[Prioritized]

## Requirement map
| Requirement | Evidence | Gap | Fix |

## Concrete rewrites
### Before
...
### After
...
### Verify
...

## Priority fixes
1. [Highest leverage]
2. ...

## Definition of done
[What a finished revision includes]
```
