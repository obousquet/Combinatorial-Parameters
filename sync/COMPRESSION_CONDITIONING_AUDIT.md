# Proper unlabeled compression and conditioning

September 20, 2026. The former `c_monotonic: true` entries for pUSC and
psUSC relied only on appending fixed examples, compressing, and erasing
fixed coordinates from the selected key. Those entries are withdrawn to
**unknown**, not changed to false. Projection monotonicity is unaffected.
The database schema uses an absent flag for an unknown classification.

## A concrete failure of the proposed construction

Let H={(1,0),(1,1)} on coordinates (a,x). Give the decoder the fixed outputs
rho(empty)=(1,0), rho({a})=(1,1), rho({x})=(1,1).
On a realizable sample, select {a} when both a and the label x=1 occur;
select {x} when x=1 occurs without a; otherwise select empty.
This is a proper unlabeled scheme of width one on all six realizable
partial samples, including the empty sample.

Condition a=1. The samples x=0 and x=1 extend respectively to samples whose
selected keys are empty and {a}. Erasing a sends both to empty, although
their x labels differ. No decoder of that erased key can serve both.
Thus the proposed construction fails even when the conditioned coordinate
was already constant. It is insufficient to assert that each original
reconstruction was proper: reconstruction must remain a function of the
new key alone.

This is not a counterexample to conditioning monotonicity. The conditioned
class is the one-coordinate full cube and has a proper stable width-one
scheme (empty decodes zero; {x} decodes one). The original class also has
such a scheme by adjoining the constant to each decoded word. Both values
are exactly one, because width zero cannot reconstruct both x labels.
The exhibited alternative original encoder is not stable: deleting x from
the sample (a=1,x=1), whose key is {a}, changes reconstruction.

## Stable variant and remaining question

The psUSC record used the same erasure sentence and additionally asserted
that stability survives. The example above does not refute a transformation
restricted to stable encoders. Nevertheless that sentence does not define
a decoder after erasure or prove collision compatibility. No separate
argument establishing that compatibility was supplied in the record.
The stable flag is therefore also unverified, not refuted. A valid general
transformation, a stability-specific collision theorem, or a genuine value
counterexample is still needed before either flag can be restored or denied.

Run `python3 sync/verify_compression_conditioning_erasure.py` to replay the
finite example and the distinction from a value counterexample. This audit
does not alter any established relationship or claim that the missing
monotonicity theorem is false.
