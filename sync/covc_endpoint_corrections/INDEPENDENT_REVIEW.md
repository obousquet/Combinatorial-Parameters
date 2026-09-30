# Q2i independent bounded review — accepted

Accepted the two authored source replacements and five canonical DB corrections in the pinned manifests below. Scope is the finite coVC model, explicit hollow-star/ample proof contracts and listed endpoints. This is not a whole-paper or full database proof audit. No sibling sources were edited.

## Source proof and negative endpoint

Read the original main.tex1163–1169, ex:maxclasses and its proof, the complete SOURCE.patch, and selected existing PartialCubes/YangDim ample/complement contracts identified in SOURCE_REVIEW.md. The complementary-cube identity is correct for a nonempty proper finite class: a minimally unrealizable partial labeling corresponds exactly to an inclusion-maximal complementary extension cube, with dimension n minus the number of specified coordinates. The correction makes dimension explicit, fixes the family type and handles the full cube separately. The lemma does not assume an undefined minimum for empty complement. The excluded empty-class case is not silently assigned a VC convention.

The repaired ample proof correctly complements AFTER projecting. Projection preserves ampleness; complement preserves ampleness; nonempty ample classes have connected one-inclusion graphs. A missing hollow-star center is isolated in that complement, so it is the sole vertex. The projected class is therefore a punctured cube and shatters every proper subset, giving coVC<=VC+1. The empty-star case is separate. Read the supporting finite complement/ample contracts in PartialCubes/main.tex577–598,8345–8363 and YangDim/ample_cohen_macaulay.tex1938–1950. These are reused existing contracts, not newly verified primary-literature imports. The later infinite-domain sentence is valid under the explicit finite-projection interpretation of extremality and finite hollow-star supports; arbitrary infinite inconsistent samples remain outside this review.

The punctured cube on n>=1 coordinates is ample: all proper coordinate sets are both shattered and strongly shattered, fixing an omitted coordinate to1. Its VC is n-1 and coVC is n. This refutes the alleged exceptional improvement, including the one-coordinate singleton case. The unsupported proposed extension to merely maximal classes is removed without being declared refuted. The retained intersection-closed argument and nearby infinite-domain examples were not re-audited.

## Canonical database corrections

Parameter042 now explicitly takes a supremum over finite hollow-star supports, with zero when none exists and infinity for unbounded sizes. On finite ground this is a maximum when a hollow star exists. It correctly distinguishes a singleton class on nonempty domain (coVC1) from a full cube (coVC0) and from the family of all singleton concepts. Finite consistency-dimension equivalence follows by minimal inconsistent restrictions; arbitrary infinite equivalence is expressly withheld. Conditioning monotonicity is repaired correctly for finite-coordinate conditioning (as its evidence and comments now specify): combine the fibre's missing center with fixed labels, choose a minimal inconsistent subset, and note every star coordinate must remain because deleting that coordinate is already realizable in the fibre. This yields an original hollow star of size at least the fibre star, without the false assertion that appending fixed labels itself gives a hollow star. Empty fibre coVC0 is compatible with this finite definition.

Relationship181 is correctly refuted at the stated-domain singleton endpoint E0/coVC1. For hollow-star size>=2, two realized neighbours disagree at each star coordinate; separating sizes0/1 proves coVC<=max(1,E). The replacement claims only this elementary bound and a strict finite counterexample, not an unbounded-ratio/functional separation or a new graph edge.

Read the actual benchmark class definitions. Half-intervals are nonempty prefixes {[i]:1<=i<=n}, so coordinate1 is fixed and gives coVC1. At n2 its two traces10/11 have no hollow2-star; at n>=3 coordinates2/3 give traces00/10/11 and coVC2. A hollow star of size>=3 contains incomparable neighbours, excluding larger stars in a chain. Values025/027 are full cubes at n1 and therefore coVC0; their size2 stars for n>=2 and elementary upper bounds give coVC2. Retained omega1 metadata is asymptotic and is not contradicted by the isolated n1 zero endpoint. The three exact value repairs are accepted.

## Computation and preservation

Read verify_covc_endpoints.py: it explicitly computes projected traces/hollow stars, shattered supports, effective coordinates, complementary maximal cubes and every nonempty conditioned fibre. Its ample criterion is the finite sandwich equality |Sh(H)|=|H|. Independently reran it:274 nonempty classes on at most3 coordinates, including144 ample classes, pass the cube formula, max(1,E) bound and conditioning checks; benchmark families and punctured cubes through6 coordinates pass. This is finite regression evidence, not a proof for all classes. General acceptance rests on the arguments above.

Checked all five staged/original DB hashes against DB-manifest.json. Original records and withdrawn authored blocks are preserved. git apply --check accepts SOURCE.patch against the current baseline. SOURCE-manifest records the expected complete resulting-source hash without writing an extra full manuscript into the constrained /tmp filesystem. This review signs the exact patch and baseline, not a fresh build. Root owns final composition, generation, builds and rendered checks. The consumer inventory remains navigation rather than certification of all its unchanged records.

## Hash pins

- `SOURCE.patch`: `17a0610093887d70f2fe4f8a311454b50f722725b124fabc8c6400c13bf6ad59`.
- `SOURCE-manifest.json`: `0172017497f8a95c8dd6939ae7337402ec63f5e29e8343b1009403b6c9635ce1`.
- `SOURCE-withdrawn.tex`: `4854258de24ab056225c4c8b46bdb1d865e014c777f3c8f73d3da974cb919f85`.
- `SOURCE_REVIEW.md`: `2d53ddc2f9921c81d23da16d61c0ad278150cf0f52a21f1a7087749d768a3db1`.
- `DB-manifest.json`: `9a577f8b6c5dd754fe858133aa091792b09a22e3cca36481a6360b62b720eadf`.
- `CONSUMERS.json`: `302c6b205b033cc1a6deba2f00441f20e3838730000edaba06d6d90d9b7e4411`.
- `verify_covc_endpoints.py`: `d9e912cec9b25269c911dc31cc78aea21824ed836efce07d740e7bc43d59c6e5`.
- Source baseline: `b1ebb2c29a719ac79acf635e982b58ea28f4e474fe48a7f9e25bfe942206907a`; expected composed source: `18b047e17b4868477b3f16ca4480a3e3e8d034c40367676c44892489cb644ffe`.
- `data/parameters/042_covc_dimension.json`: `e29aa256db307153a80712ff4eb39273d323aa155b21a4dc04df05227e219a53`; preserved original `704ebd7e38ead06cfc05e41e7571b684ccbb7dd5f797416c119eb363bf8e00ba`.
- `data/relationships/181_effective_range_covc_dimension.json`: `8b04f40cae0c332ff18c43eca1afa4b7d7559eb6f5c9f813da21b4f145a17aec`; preserved original `c261eeaf33eee163423a0cec5b8dbe8419a0874c0e70efdec1d982ac3a150564`.
- `data/values/023_covc_dimension_halfintervals.json`: `5e88e7dae941406d0456c382d0b4ec366e1576af35272fddb09a82774f7d89a9`; preserved original `8052b847e28d5d7659cd46adffd5636f4ded94007b535fb3a4d399849c679c4e`.
- `data/values/025_covc_dimension_singletons_plus_empty_set.json`: `afc7c6b47bac5a7c694228586f9c2ded95f1d6497b91519de6031eddbd1bde20`; preserved original `d4b9342466ae3533defcf480038709bd8b1315ef8a7a69a285dff715f89a5d10`.
- `data/values/027_covc_dimension_trivial_concepts.json`: `ef960ec001597fa9912477039370d3165901efc927150ab5275d81b2e5e58c95`; preserved original `696165ba3097aeca9409d1f2f2f0555aec84427349c3434cedaff74224d7594d`.

## Accepted propagation addendum: derived relationship343 and values963/965/966

Reviewed the separately staged four-record derived packet. Relationship343 inherits181's invalid unshifted bound by maximizing over subfamilies. The same one-concept class on one coordinate has coVC*=1 (its only subfamilies are itself and empty) but E=0. Status refuted and a strict finite witness are correct; the obsolete machine derivation tag is removed while the original derivation is preserved. Applying the valid max(1,E) bound separately to every subfamily yields the stated corrected bound without creating a new graph edge.

The envelope endpoint value963 is1 at n1, because the full one-cube has a singleton subfamily of coVC1; ambient dimension bounds it above. At n>=2 the two constants have coVC2 and every subfamily has at most two concepts, excluding hollow stars with more than two distinct leaves. Thus its corrected piecewise value is sound. Values965/966 remain n: the singleton-concepts subfamily witnesses the lower bound, and the ambient n-coordinate domain supplies the upper bound. Their revised proofs no longer rely on the false unshifted effective-range edge. These are accepted proof/endpoint repairs, not newly claimed asymptotic separations.

Independently searched every relationship derivation field for either effective_range_covc_dimension or effective_range_monotonic_covc_dimension:343 was the only explicit derivation consumer of181; no further explicit derivation consumed343. Also read all five envelope value records963/964/965/966/971. Value964 already uses the valid ambient bound and explicitly handles E0;971 uses ordinary coVC and the distinct star-plus-one affine bound, not181/343. This is an exact dependency screen, not blanket recertification of971 or all transitive mathematical consumers. Root must still regenerate/check the published graph so refuted181/343 contribute no asserted edges.

The initial source/DB acceptance remains unchanged. The following pins add the four-record packet and supersede only the earlier consumer-inventory fingerprint after its scope expansion. Original bytes were checked against this supplemental manifest.

- `data/relationships/343_effective_range_monotonic_covc_dimension.json`: `0ec473e8204156544cf36d123fa19e130f8d9d24c4747449c64d43d10064e957`; original `3c0ebf1039f147ecd7b9b3d0087e59dcffe6e258bd3e39477e8eef8e0194cb1d`.
- `data/values/963_monotonic_covc_dimension_trivial_concepts.json`: `9cc44cb92928cf7ea299f96af58304c915064dfa608a82d2d4f1d40d0231d62e`; original `7041c439c920dc5faf6f3d91cd1c8fe9bb1283a1d2f60f93b83f3759082f58d2`.
- `data/values/965_monotonic_covc_dimension_full_cube.json`: `3c237b6e10f3fcfb0f4ad15e8be8ab03324af1a7f41fb2b340abe7ee360db0e1`; original `5eb3eabd45d97d0ed14560ac732ac4a1120ac3173ecaaf857f8be753aa3603b1`.
- `data/values/966_monotonic_covc_dimension_singletons_plus_empty_set.json`: `febabf0c23d55f6b63dadbd16a7efd130a9286f77034ec53158eece9a2d08561`; original `3d2895d956a40917224028ee2ec28bc5e24cbdef9e45814270a85bd635a4ec9d`.
- `DB-derived-manifest.json`: `44bd4d84b0d74bda63b5ea10b483bf4c33e61f047060ad24fd3f649fd6db5176`.
- `CONSUMERS.json`: `714a5e88de1159ab71263156f44b317fdc34d58afa972530dc80d8ff54d0092f`.
- `CONSUMERS.md`: `78e987678187d85410ea7708bf36742db434324dbfb4a95893689309a21fef7a`.
