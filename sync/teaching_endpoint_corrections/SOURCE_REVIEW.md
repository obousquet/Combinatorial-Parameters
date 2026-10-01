# Q2k CP-D17 source-contract review

**Decisive finding:** The binary inclusion-forcing quantity defined at CP main.tex2529–2530 is bounded above by ordinary teaching dimension. The cited proof's underlying argument is valid. The author warning does not identify a counterexample or a genuine obstruction: a teaching sample is automatically an inclusion-forcing sample. Preserve the warning as historical text when repairing this block, rather than converting it into a claimed source error.

## Primary source and provenance limits

The pre-existing shared packet `ResearchWork/literature/math/goldman1995complexity` contained metadata and publisher-record summaries only; it did not contain a checked proof. Shared-library searches preceded browsing. The publisher DOI is10.1006/jcss.1995.1003, journal citation *Journal of Computer and System Sciences*50(1),20–31(1995).

The author-hosted primary PDF is https://www.cis.upenn.edu/~mkearns/papers/teaching.pdf, **WUCS-92-28, August11,1992,29pages**. It is an earlier technical-report version, not the1995 journal layout. Browser reading checked the teaching definition in §2 (internal p.3), relevant §4.1 example (internal p.9), and the entire §4.2 definition, attributed Natarajan theorem, Lemma6 and Corollary7 (internal pp.11–12; PDF page indices10–11). Parent owns acquisition into the existing packet. Do not assert that final-journal numbering or every byte of its proof was checked merely from this report.

The report's Lemma6 explicitly states td≥nd and proves it using a teaching sequence as the required nd sample. This is the same direct argument justified below. The report's definition requires c⊆c′ for **every** consistent c′, including c itself; the survey instead says “any other concept” and uses a strict-subset glyph. On distinct concepts these are equivalent, but the repair should use non-strict inclusion uniformly to eliminate ambiguity.

## Exact local contract and checked proof

Let X be finite and H a nonempty family of subsets of X. For h∈H define its inclusion-forcing sample size as the minimum |S| over S⊆X such that

`h′|S = h|S, h′∈H  =>  h⊆h′`.

The class quantity is the maximum over h. Samples are labeled by h; their size should be **at most** the stated uniform bound, avoiding unnecessary exact-cardinality/padding wording. This quantity is what the source calls Natarajan's dimension measure for Boolean-function classes. It is not the standard multiclass Natarajan shattering dimension (which reduces to VC dimension for binary labels). The familiar name alone is insufficient to identify the parameter.

For each h, take a minimum ordinary teaching sample S_h. Its only consistent class member is h, and h⊆h. It therefore satisfies the inclusion-forcing condition, giving the targetwise inequality nd_H(h)≤TD_H(h). Maximizing proves nd(H)≤TD(H). This proof works for every finite binary class on an arbitrary finite ground set; no Boolean-input arity or additional closure property is needed. The source's contradiction presentation fixes an arbitrary target and abbreviates this targetwise reasoning; that abbreviation does not invalidate the argument.

For a singleton class the empty sample works for both quantities, so both are zero. For X empty the unique nonempty class is a singleton and the same endpoint applies. Empty classes should remain excluded unless a separate maximum-over-empty convention is expressly adopted. Nonempty classes with more than one member have nd≥1: if every target required no examples, every pair would contain each other and hence coincide. The bound has no asymptotic constants and no sample-compression, random-query or learner-randomization assumptions.

A source-owned distinction from binary VC is already available in the report's Lemma3: the coded-singleton construction has teaching size one and arbitrarily larger VC dimension. Consequently its inclusion-forcing nd is one while its binary multiclass-Natarajan dimension is VC. Reuse that example or the existing catalogue addressing/coded examples if the manuscript needs an illustration; no new example family is required.

## Adjacent VC attribution must not be silently copied

The report attributes to Natarajan the inequality `nd(C_n)≤VC(C_n)≤n nd(C_n)` for classes of Boolean functions **over n input variables**, whose instance domain has2^n points. The survey instead writes `VC≤E.ND`. Its E is the existing effective-range parameter, not the source's Boolean-input arity. These coefficients are not interchangeable as an exact citation.

Under the survey's finite binary definitions, VC≤E·nd is a weak elementary consequence: VC≤E always; if H has more than one member then nd≥1; and singleton classes have VC=nd=0. Thus this written inequality need not be false, but the current attribution does not match the checked source statement and is uninformative in this form. The minimal repair should omit it or explain the exact source domain/arity separately. No primary Natarajan paper has been checked in this bounded task, so the stronger reported nd-versus-VC theorem should not be newly promoted here.

## Recommended minimal source disposition

1. Rename the heading to make its historical binary inclusion-forcing meaning explicit, and give the finite nonempty-class formula with consistent non-strict inclusion.
2. Retain nd≤TD with the short targetwise proof above, cite Goldman–Kearns's discussion with the version limitation recorded in the audit, and remove the unsupported bug warning from active prose.
3. Avoid the overloaded modern multiclass name without an explicit distinction. Do not introduce a new catalogue parameter or claim that it is the multiclass Natarajan dimension.
4. Remove or narrowly correct the adjacent E-based attribution. This review does not import the underlying Natarajan theorem from a secondary attribution.
5. Preserve the exact original block and stage any future patch for independent review. No authored source or sibling file was changed for this report.

## Scope and evidence boundaries

Read the current CP block and immediate hitting/teaching context, the shared packet metadata, and the primary report sections above. A current research-knowledge context was read; it yielded navigation and unrelated raw excerpts, not proof authority. Bounded sibling searches did not reveal a competing current ND owner. Database consumers are a separate assigned audit. The broader hitting definition, relative-hitting equality, doubling-dimension definition, and other Goldman–Kearns theorems are not certified here. This is recovery of an elementary existing argument, not new mathematics or full-paper review.
