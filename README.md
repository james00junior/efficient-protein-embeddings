# Efficient Protein Embeddings

## Engineering the Smallest Useful Protein Representation

This repository contains an engineering study of protein embedding dimensionality reduction with a focus on the practical cost of high-dimensional representations.

The central question is:

> **How much dimensionality can be removed from protein embeddings while preserving useful biological signal?**

Protein foundation models can produce embeddings with hundreds or thousands of dimensions. At scale, that dimensionality directly affects storage, memory, data movement, vector indexes, and downstream computation. This project studies the accuracy--efficiency trade-off rather than assuming that the original embedding dimension is automatically necessary.

## Research objective

For an embedding dimension $D$, we evaluate whether a smaller representation $d < D$ preserves downstream biological utility.

The engineering objective is:

$$
\min_d C(d)
\quad \text{subject to} \quad
Q(d) \geq Q_{min}
$$

where:

- $d$ is the retained embedding dimension;
- $C(d)$ is the engineering cost associated with that representation;
- $Q(d)$ is downstream task utility;
- $Q_{min}$ is the minimum acceptable utility.

The deployment rule is therefore:

$$
d^* = \min \{d : Q(d) \geq Q_{min}\}.
$$

This makes dimensionality a deployment decision rather than simply a model-architecture parameter.

## Why dimensionality matters

For $N$ protein embeddings stored as FP32 vectors:

$$
S_{flat} = 4ND
$$

Reducing the representation from $D$ to $d$ gives:

$$
S_{reduced} = 4Nd.
$$

For example, reducing a 768-dimensional FP32 representation to 256 dimensions gives:

- **3x smaller representation**
- **66.7% reduction in storage**
- lower memory requirements
- less data movement
- smaller vector indexes
- potentially lower downstream compute

For one million vectors:

| Representation | FP32 storage |
|---|---:|
| 768 dimensions | ~3.07 GB |
| 256 dimensions | ~1.02 GB |
| Savings | ~2.05 GB |

The same relationship scales approximately linearly with the number of stored vectors.

## Experimental design

The current experiments use protein embeddings derived from the ESM-2 representation and evaluate dimensionalities:

$$
D \in \{32,64,128,256,512,768,1024,1280\}.
$$

The analysis evaluates multiple remote-homology targets and biologically meaningful holdout regimes:

- class label
- family label
- fold label
- superfamily label
- family holdout
- fold holdout
- superfamily holdout

Metrics include:

- accuracy
- Macro-F1
- balanced accuracy
- explained variance
- train/validation/test performance

The purpose of the holdout analysis is important: a representation that performs well when related examples are present in training may behave very differently when evaluation is performed at a more distant biological level.

## Current results

The experiments show that there is **no single dimensionality that is uniformly optimal across all target/holdout combinations**.

Examples from the current results:

| Target | Holdout | Best D by accuracy | Test accuracy | Test Macro-F1 | Balanced accuracy |
|---|---|---:|---:|---:|---:|
| class | family | 768 | 0.9827 | 0.9798 | 0.9721 |
| class | fold | 768 | 0.8900 | 0.7602 | 0.8857 |
| class | superfamily | 1280 | 0.9282 | 0.8718 | 0.8378 |
| family | family | 1024 | 0.9623 | 0.9146 | 0.9374 |
| fold | family | 768 | 0.9796 | 0.9497 | 0.9603 |
| fold | fold | 1024 | 0.3162 | 0.1286 | 0.1778 |
| fold | superfamily | 1280 | 0.6196 | 0.3492 | 0.3872 |
| superfamily | family | 768 | 0.9788 | 0.9430 | 0.9627 |
| superfamily | superfamily | 1280 | 0.5774 | 0.3589 | 0.4219 |

These results should be interpreted as an engineering characterization of the current experimental setup, not as a claim that a particular dimension is universally optimal for protein representation.

### Key observation

The results demonstrate the central engineering trade-off:

> **Lower dimensionality can substantially reduce representation cost, but the amount of dimensionality that can be removed depends on the biological task and evaluation regime.**

For example, some tasks retain strong performance at 256--768 dimensions, while harder distribution shifts continue to benefit from higher-dimensional representations.

This motivates selecting dimensionality using an explicit utility threshold rather than applying a fixed compression ratio everywhere.

### Full dimensionality sweep: class-label / family holdout

The class-label experiment provides a clear example of the accuracy--dimension relationship:

| D | Test accuracy | Test Macro-F1 | Explained variance |
|---:|---:|---:|---:|
| 32 | 0.8373 | 0.6241 | 0.7676 |
| 64 | 0.9009 | 0.8220 | 0.8326 |
| 128 | 0.9607 | 0.9147 | 0.8906 |
| 256 | 0.9764 | 0.9709 | 0.9399 |
| 512 | 0.9811 | 0.9789 | 0.9768 |
| 768 | 0.9827 | 0.9798 | 0.9909 |
| 1024 | 0.9827 | 0.9799 | 0.9973 |
| 1280 | 0.9827 | 0.9799 | 1.0000 |

The important engineering observation is that the curve shows strong gains from 32 to 256 dimensions, followed by progressively smaller improvements. In this experiment, 768 dimensions reaches the maximum observed test accuracy, while 1024--1280 dimensions provide essentially no additional accuracy gain.

This motivates an explicit cost/utility selection rule: if a deployment target can accept a small utility difference, a substantially smaller representation may be sufficient.

### Dimensionality and explained variance

Across the sweep, explained variance increases monotonically with retained dimension:

| D | Explained variance |
|---:|---:|
| 32 | 0.7676 |
| 64 | 0.8326 |
| 128 | 0.8906 |
| 256 | 0.9399 |
| 512 | 0.9768 |
| 768 | 0.9909 |
| 1024 | 0.9973 |
| 1280 | 1.0000 |

This also highlights an important methodological point: **variance preservation is not the same as downstream biological utility**. A representation can retain high variance while task performance behaves differently.

### Generalization across biological holdouts

The holdout experiments reveal a stronger effect than the raw dimensionality curve alone.

For the class-label target:

- family holdout reaches 0.9827 test accuracy at D=768;
- fold holdout reaches 0.8900 at D=768;
- superfamily holdout reaches 0.9282 at D=1280.

For fold-level prediction:

- family holdout reaches approximately 0.9796 at D=768;
- fold holdout remains only 0.3162 at D=1024;
- superfamily holdout reaches 0.6196 at D=1280.

For superfamily prediction:

- family holdout reaches approximately 0.9788 at D=768;
- superfamily holdout reaches 0.5774 at D=1280.

These results show that **evaluation regime can matter as much as dimensionality**. Increasing D does not automatically solve a difficult biological generalization problem.

### Label-space limitation

One superfamily/fold combination was not evaluated because the test set contained labels that were not present in the training set. This is a genuine label-space limitation rather than a model-performance result, and it is retained as an explicit limitation in the experimental record.

## Measured engineering benchmark

The biological experiments were followed by a measured engineering benchmark using 10,000 training vectors and 718 test vectors across the same dimensionality sweep.

The benchmark measured:

- PCA transformation time
- classifier fitting time
- classifier inference time
- inference throughput
- representation memory
- storage reduction
- compression ratio

Measured results:

| D | PCA transform (s) | Classifier fit (s) | Inference (s) | Inference vectors/s | Memory reduction | Storage reduction | Compression |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 0.0649 | 53.6069 | 0.0141 | 50,914.6 | 97.5% | 97.5% | 40.00x |
| 64 | 0.0622 | 54.7292 | 0.0128 | 56,065.3 | 95.0% | 95.0% | 20.00x |
| 128 | 0.0756 | 55.7735 | 0.0148 | 48,402.6 | 90.0% | 90.0% | 10.00x |
| 256 | 0.0940 | 69.9802 | 0.0235 | 30,577.0 | 80.0% | 80.0% | 5.00x |
| 512 | 0.0898 | 90.3026 | 0.0288 | 24,925.2 | 60.0% | 60.0% | 2.50x |
| 768 | 0.1149 | 112.2500 | 0.0364 | 19,702.8 | 40.0% | 40.0% | 1.67x |
| 1024 | 0.1527 | 134.2794 | 0.0518 | 13,870.0 | 20.0% | 20.0% | 1.25x |
| 1280 | 0.1452 | 164.1449 | 0.0463 | 15,493.5 | 0.0% | 0.0% | 1.00x |

### Engineering interpretation

The measured benchmark makes the storage/computation trade-off concrete.

- Reducing 1280D to 256D removes **80% of the representation storage** and gives a **5x smaller vector representation**.
- Reducing 1280D to 128D removes **90% of storage** and gives a **10x compression ratio**.
- Reducing to 32D removes **97.5% of storage** and gives a **40x compression ratio**.
- Classifier fitting time increased from approximately **53.6 seconds at 32D to 164.1 seconds at 1280D** in this benchmark.
- Inference timings were not strictly monotonic, so they are reported as measurements rather than interpreted as a universal scaling law.

For the class-label/family-holdout experiment, test Macro-F1 was approximately 0.9709 at 256D, 0.9789 at 512D, 0.9798 at 768D, 0.9799 at 1024D, and 0.9799 at 1280D. This provides an engineering example where substantial dimensionality reduction is possible with little observed downstream utility loss.

The benchmark was run on the local experimental environment and should therefore be treated as a machine/software-specific measurement rather than a universal hardware performance claim.

## Cost model

A first-order engineering cost model treats storage, representation memory, data movement, and dimension-scaled similarity computation as approximately proportional to $D$.

For a representation reduced from 1280D:

| D | Storage reduction | Compression | Relative dimension-scaled cost |
|---:|---:|---:|---:|
| 32 | 97.5% | 40.00x | 2.5% |
| 64 | 95.0% | 20.00x | 5.0% |
| 128 | 90.0% | 10.00x | 10.0% |
| 256 | 80.0% | 5.00x | 20.0% |
| 512 | 60.0% | 2.50x | 40.0% |
| 768 | 40.0% | 1.67x | 60.0% |
| 1024 | 20.0% | 1.25x | 80.0% |
| 1280 | 0.0% | 1.00x | 100.0% |

This is intentionally a transparent first-order model, not a monetary cloud-cost estimate. Actual infrastructure costs depend on hardware, indexing strategy, batch size, concurrency, storage tier, network topology, and workload characteristics.

## Biological hierarchy

Protein biology provides a natural hierarchy:

**Superfamily → Family → Fold/Domain → Protein/Sequence → Residue**

This suggests a second engineering direction beyond flat dimensionality reduction.

A hierarchical representation can be expressed conceptually as:

$$
x_i \approx h_{g_i} + r_i
$$

where:

- $h_{g_i}$ is a representation shared by a biological group;
- $r_i$ is the protein-specific residual.

A possible storage model is:

$$
S_{hier} = 4Gd_h + 4Nd_r
$$

where $G$ is the number of biological groups, $d_h$ is the shared representation dimension, and $d_r$ is the residual dimension.

When $G \ll N$, this may provide an additional storage advantage.

**This hierarchical storage formulation is currently a testable engineering hypothesis, not a demonstrated result of the present experiments.** Future experiments will measure whether shared biological representations plus residuals can preserve downstream utility while reducing total storage.

## Engineering perspective

This project treats embeddings as production data assets.

The relevant cost is not only model inference. A production system may repeatedly pay for:

1. embedding generation
2. persistent storage
3. memory loading
4. network transfer
5. vector indexing
6. nearest-neighbour search
7. downstream model input
8. backup and replication

Reducing dimensionality can therefore create savings across the entire representation lifecycle.

The objective is not maximum compression. It is:

> **the smallest representation that satisfies the required biological utility.**

## Repository structure

The repository is intentionally kept lightweight. Large raw datasets and generated embedding stores are not intended to be committed directly to Git.

A planned structure is:

```text
efficient-protein-embeddings/
├── README.md
├── data/
├── embeddings/
├── notebooks/
├── src/
├── results/
├── docs/
└── tests/
```

Large datasets and model-generated embedding matrices should be stored outside normal Git history or handled through an appropriate large-file/data-storage mechanism when required.

## Reproducibility

The experiments should record:

- Python version
- package versions
- embedding model
- source dataset
- embedding dimension
- dimensionality-reduction method
- random seed
- classifier configuration
- train/validation/test split
- holdout definition
- evaluation metrics
- benchmark hardware

The goal is to make every reported result traceable to a specific experiment configuration.

## Scope and limitations

The current study has several important limitations:

- The present experiments focus on a specific protein embedding model and remote-homology benchmark.
- Results depend on the selected classifier, splits, and evaluation protocol.
- Dimensionality reduction can preserve variance without necessarily preserving task-relevant biological information.
- Accuracy alone is insufficient for imbalanced biological classification; Macro-F1 and balanced accuracy are therefore also reported.
- The engineering benchmark is based on a local environment and relatively small vector counts, so measured timings should not be generalized directly to production-scale infrastructure.
- The first-order cost model is dimension-scaled and is not a monetary cost model.
- The superfamily/fold holdout experiments expose difficult generalization regimes, including cases where labels are poorly represented or absent in training.
- Hierarchical shared-representation storage has not yet been experimentally validated.
- Exact vector-search benchmarking is the next systems experiment; current search-cost discussion is therefore analytical rather than a measured vector-search result.

These limitations define the next experimental steps rather than weakening the engineering objective.

## Roadmap

### Phase 1 — Baseline dimensionality study

- [x] Establish protein embedding dimensionality experiments
- [x] Evaluate multiple dimensions
- [x] Evaluate multiple biological targets
- [x] Evaluate family/fold/superfamily holdouts
- [x] Record accuracy, Macro-F1, balanced accuracy and explained variance
- [x] Consolidate experimental results
- [ ] Add automated result generation
- [ ] Finalize reproducibility metadata

### Phase 2 — Engineering cost analysis

- [x] Calculate storage per dimension
- [x] Calculate compression ratios
- [x] Calculate representation memory requirements
- [x] Measure dimensionality-dependent compute
- [x] Measure classifier inference throughput
- [x] Produce first-order cost model
- [ ] Measure vector-index footprint
- [ ] Benchmark exact vector search
- [ ] Produce empirical utility-vs-search-cost Pareto curves
- [ ] Define utility-threshold dimension selection

### Phase 3 — Additional biological datasets

Evaluate whether the same engineering behaviour appears across other protein tasks and datasets, including additional enzyme/protein classification benchmarks.

The objective is to determine whether the observed dimensionality trade-off is specific to remote homology or generalizes across biological representation tasks.

### Phase 4 — Hierarchical representations

- [ ] Construct biological group representations
- [ ] Model protein-specific residuals
- [ ] Compare flat and hierarchical storage
- [ ] Measure retrieval and downstream utility
- [ ] Quantify storage and compute savings

### Phase 5 — Production-scale evaluation

- [ ] Evaluate million-scale embedding stores
- [ ] Measure serialization and loading time
- [ ] Benchmark vector indexing
- [ ] Evaluate memory and data-transfer costs
- [ ] Produce deployment-oriented cost models

## Research philosophy

The project is deliberately engineering-oriented.

The question is not:

> "Can we compress protein embeddings?"

The more useful question is:

> "What is the minimum representation required for a given biological workload, and what engineering cost does that choice create?"

This reframes dimensionality reduction as a systems optimization problem spanning biological utility, storage, memory, compute, and infrastructure.

## Status

**Active research / engineering study**

The repository contains the experimental foundation, biological dimensionality results, and the first measured engineering benchmark. The next step is to add measured vector-search behaviour and then consolidate the empirical utility/cost trade-offs.

## License

License and dataset-specific usage terms will be documented before redistributing any third-party data or derived artifacts.
