# Q2h independent bounded review

Accepted. The DB133 source-title typo has been corrected to *The Power of Random Counterexamples* and its refreshed hash checked. The review is limited to the changed source proof/model, eleven DB records and the direct-consumer inventory. It is not certification of the full primary paper or survey.

## Authored proof and finite witness

Read the complete final SOURCE.patch and proposed model/proof block. The weighted medoid proof is valid: with a_g the fraction agreeing with g, the difference between target and proposal distances cancels outside D(g,t), while inside it equals sum mu(x)(2a_g(x)-1). Minimality makes the sum nonnegative. Conditioning the example law on D then eliminates at least half the version space in expectation. The factor m converts proportions into counts correctly. Rejection leaves between1 and m-1 candidates, so induction applies to every subsequent target/version space with the same conditional sampling rule; pairwise positive disagreement mass persists. Jensen uses log base2. The agreement case is separately bounded by1<=log2 m for m>=2; initial singleton cost is0. This proof does not require uniform target posteriors or strictly more than half elimination. The Max-Min numerical bound is attributed separately from the manuscript's weighted closest-to-average algorithm.

Independently checked the final five-coordinate witness as the existing DB020 coded-singleton class at n=3, after coordinate permutation and assignment of codes00/01/10/11. It is stronger than the preparatory six-coordinate improper example because zero is now a proper concept. VC is exactly2. Querying zero costs1 for that target; for a nonzero target with k positive code bits it costs1+k/(k+1). A primary reply leaves one candidate; a code reply leaves two; one proper query always distinguishes two. The maximum5/3 is an upper bound, not an asserted optimum. Uniform full support satisfies both random models. Thus DB025's exact pointwise coefficient-one lower bound is refuted without asserting any unbounded ratio or refuting a worst-distribution asymptotic theorem.

The deterministic adaptive learner/count-all/identification-stop clauses align source and DB050/051. The archived adjacent exploratory paragraph used removed quantities and does not supply a retained stronger claim. The old proof/paragraph remain in SOURCE-withdrawn.tex; original records are preserved separately.

## Selected primary-source contract

Read official canonical original.pdf via its source.txt extraction, specifically Theorem21 and preceding Max-Min/T(n) definitions (internal pp10–11, text lines533–590), Theorem25 and proof (internal p12, lines653–662), and the flagged posterior sentence in Theorem12 (internal p7, lines327–340). The source fixes proper hypotheses and a known example law; Theorem21's T(n) maximizes over target and distribution, uses singleton0 and proves the log2 n numerical upper bound. The new independent weighted proof handles agreement explicitly. This review does not re-certify the entire Max-Min dependency chain.

Theorem25 states Omega(d), and its proof chooses a distribution concentrated on a shattered set. It does not support the removed coefficient-one pointwise claim. The flagged posterior assertion in Theorem12 is indeed invalid as stated: under uniform target on the two-bit cube, uniform example law, query00 and counterexample at coordinate1, targets10 and11 have likelihoods1 and1/2 and hence posterior masses2/3 and1/3. This identifies a proof-step problem, not a counterexample to the theorem's m-1 lower bound. No replacement general lower theorem is certified or imported. SOURCE_REVIEW.md preserves this limitation appropriately.

## Database, preservation and consumers

Read all eleven staged records against their preserved originals. DB025 retains endpoints/type as a refuted attempted comparison, links the unique survey witness label and records only a strict finite gap. DB133 retains the valid bound, removes the duplicated flawed proof and points to the unique weighted-proof label; singleton-plus-empty still gives its unbounded reverse ratio. Definitions050/051 clarify rather than conflate learner and oracle randomization.

Values738/739/766/774 retain established upper bounds n, using the class cardinality2^n. Verified majority's actual definition has exactly one concept per n-bit word. Values758/771 retain the complete-code restriction n=2^r and bound r; no arbitrary-code exact formula is asserted. Value756 retains the floor(log2 n) upper bound through the existing adversarial/Littlestone dictionary; read the universal-class definition and existing value701's balanced-tree/leaf-count proof. The seven records remove value_class lower-growth metadata and explicitly withdraw exact equality without asserting equality false for every distribution. No new exact random-query optimum is claimed.

All eleven manifest original/new hashes were checked. Preserved-original bytes match their baseline hashes and each record identifies its intended durable correction location. The two new canonical labels resolve once in proposed SOURCE-main.tex. Direct CONSUMERS.json coverage is independently re-enumerated:2 parameter records,5 direct relationships,13 direct values; all baseline file hashes match. This is coverage verification and selective mathematical review, not a proof audit of every unchanged consumer. Source ownership remains DB→generated definitions/values/site, with handwritten full proof in survey. Preliminary proposed/ records are explicitly superseded and are not the final installation payload.

No live edits or new proof campaign were performed. Build/render validation and final DB generation/checks remain root-owned.

## Reviewed hashes

- `SOURCE-main.tex`: `b1ebb2c29a719ac79acf635e982b58ea28f4e474fe48a7f9e25bfe942206907a`.
- `SOURCE.patch`: `fde853f41d80dea55338f174ea0747a336167b8859a0c5d12b3a12751bb32af2`.
- `SOURCE-withdrawn.tex`: `edb55ebe46f0789d66c222b7bf5a2edb2f0f465448726903a7fe4da1e2183f58`.
- `SOURCE-tex-manifest.json`: `3fdd1519931513bf1fbfcc33c32d0cc111f7c080b0d8243d00af2db3726283fc`.
- `SOURCE_REVIEW.md`: `61d1202b144e2b2bf2264b440cbe04536eca9a05af4086eb3b61be8c4ac89774`.
- `CONSUMERS.md`: `77ce80d35e29ae6540b8179e91b6c2f8b664ada1e62a7775ae8b7a6069276998`.
- `CONSUMERS.json`: `fc0271c6d6f4c63bbb7a1ffad10a42a224c57f1d356861ac117672a0bce8b2f8`.
- Canonical `original.pdf`: `b99eaa39f284526b7e451dded1b04cdce19822b936bc6255a5e8421f47fce7a7`.
- Canonical `source.txt`: `14b7997261192ec391363733b3d909ebf1249d6468cf7b73a790cb0a16a21d60`.

- Final `DB-manifest.json`: `fd9256e784683ec797d5b6443b264ee9ffb4b6961825130a5d368114fa229999`.
- `data/parameters/050_random_proper_equivalence_queries_complexity.json`: `cbf4e6e88d7324ed5546b3a0906cb4b57b7ed44022aeb361e0e7346f74abdd42`; preserved original `ccd00ef62eafa1e044dbf96e3576778909d5073c99d86d030e8d391c1e4d1188`.
- `data/parameters/051_random_equivalence_queries_complexity.json`: `865231bc0a1eeff563d9cd354cc7da624d2a34a927e03ef4c1419c8e53baa50a`; preserved original `921019640a6d6defd73e2fbf237d1b24a1c71ba6915ef275f66558b80620bc81`.
- `data/relationships/025_random_equivalence_queries_complexity_vc_dimension.json`: `3936068125ee02c4643cf7ff941457bf73ba8a9fb52eac799538c32804dcb4ef`; preserved original `fa9febf2edc3e13af75ef6ab40b3a45556b3ec62373b49d21af7c6005adc73fa`.
- `data/relationships/133_log_size_random_proper_equivalence_queries_complexity.json`: `145a244a8aeff538deae9cc68326c9f8e2bb51ab2bfa2884f63ef8d88c4152e1`; preserved original `b8d2b0a6dde2bfcca71756832f803f7773870bdc7ac131cdb9239665419c1afc`.
- `data/values/738_random_equivalence_queries_complexity_full_cube.json`: `d6fc56e5d71650b587c35bcbc936402a37a36241e76cdcac2003990e92c32cc8`; preserved original `93b7fec4719aa903bda47a2a3d0f0e8175ac2b0c298cf58d3c288e441ca04b08`.
- `data/values/739_random_proper_equivalence_queries_complexity_full_cube.json`: `760b380281b7972e7431d091c9208929c85e47d5758af494bb65e41936d8719f`; preserved original `b65aa1dec9e26b0bfe6089afd01595d6dbd8bfe4589d26fa55e05d6d97c14044`.
- `data/values/756_random_equivalence_queries_complexity_universal_class.json`: `787ec1ee200758491b27dc297ea79603f83c430a675903556b88b48145dcf4c4`; preserved original `3d090a3e09902dfd27f97d50552f103cce3def4b064e93115ad511426c25dc2d`.
- `data/values/758_random_equivalence_queries_complexity_addressing.json`: `7d616d013bd3b6e0de4ad8c9b428884979e73205bede39d7383fb50af3c6a0d1`; preserved original `d2421f034fef222d91f1417e3f0d1ec2a7ef3f004b920685a633fc664ddde508`.
- `data/values/766_random_equivalence_queries_complexity_majority.json`: `95cb997f73f347b59af69879845d97fdee4093018464a042f0c7d0df70f3e6c3`; preserved original `0cf40e384f439450210b15af472879d991fed7b2f3e19664cad3b23454b647a4`.
- `data/values/771_random_proper_equivalence_queries_complexity_addressing.json`: `45778dde0d2ca8c3f0a0eb724abde9beb39b56bd04dc71d05a4950129af7fb8a`; preserved original `ace32e345d9c2bdcf5ef940e8cf1ada6c503654770604351cc09506fb464220d`.
- `data/values/774_random_proper_equivalence_queries_complexity_majority.json`: `91b4abb6bbfa2917fabb52e845257b7c2878b63ab8572bf37d374f398a2b70fe`; preserved original `a55c3e9b8350c19f2070e66501201dffb818a1690c53fc6a3ddbca6f5b91b7a4`.
