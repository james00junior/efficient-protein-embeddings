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

## Measured vector-search benchmark

The engineering study was extended with an exact vector-search benchmark using **FAISS 1.7.4** and `IndexFlatIP`. Database and query vectors were L2-normalized, making inner-product search equivalent to cosine similarity.

The benchmark used:

- 10,000 database vectors
- 718 query vectors
- $K=10$
- 5 search repeats
- dimensions $D \in \{32,64,128,256,512,768,1024,1280\}$
- exact 1280D search as the reference neighbour set

Recall@10 measures overlap with the exact 1280D top-10 neighbour set. It therefore measures **nearest-neighbour structure preservation**, not biological classification accuracy.

### Vector-search results

| D | Index memory (MB) | Latency (ms/query) | QPS | Recall@10 | Storage reduction | Compression |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 1.22 | 0.2375 | 4,210 | 0.4418 | 97.5% | 40.00x |
| 64 | 2.44 | 0.2880 | 3,473 | 0.5100 | 95.0% | 20.00x |
| 128 | 4.88 | **0.2167** | **4,614** | 0.5489 | 90.0% | 10.00x |
| 256 | 9.77 | 0.2759 | 3,625 | **0.5547** | 80.0% | 5.00x |
| 512 | 19.53 | 0.3346 | 2,989 | 0.5504 | 60.0% | 2.50x |
| 768 | 29.30 | 0.3381 | 2,958 | 0.5439 | 40.0% | 1.67x |
| 1024 | 39.06 | 0.3430 | 2,916 | 0.5403 | 20.0% | 1.25x |
| 1280 | 48.83 | 0.3938 | 2,539 | **1.0000** | 0.0% | 1.00x |

The exact baseline index required approximately 0.0084 seconds to build. Reduced-dimensional indexes were substantially smaller, with index memory decreasing from 48.83 MB at 1280D to 9.77 MB at 256D and 4.88 MB at 128D.

### Vector-search findings

Several findings are important for the engineering interpretation.

**1. Index size scales directly with dimensionality.**

For this 10,000-vector benchmark, reducing 1280D to 256D reduced the vector-index representation from approximately 48.83 MB to 9.77 MB, an **80% reduction**. At 128D, the reduction was **90%**, and at 32D it was **97.5%**.

This relationship is predictable for flat FP32 vector storage and provides a direct systems benefit independent of downstream classifier choice.

**2. Nearest-neighbour preservation does not increase monotonically with dimension.**

Recall@10 increased from 0.4418 at 32D to 0.5547 at 256D, but then remained approximately flat or decreased slightly:

- 256D: 0.5547
- 512D: 0.5504
- 768D: 0.5439
- 1024D: 0.5403

Thus, retaining additional PCA dimensions did not produce progressively higher agreement with the original 1280D nearest-neighbour structure in this benchmark.

This is an important distinction from explained variance: **preserving more embedding variance does not guarantee proportional preservation of nearest-neighbour relationships.**

**3. Search performance was non-monotonic at low dimensions.**

The fastest measured configuration was 128D at 0.2167 ms/query and approximately 4,614 queries/second. The 1280D baseline measured 0.3938 ms/query and approximately 2,539 queries/second.

The 1280D representation therefore had approximately 1.8x the measured per-query latency of the 128D representation in this benchmark. However, the measurements at smaller dimensions were not strictly monotonic, so these timings should be interpreted as empirical measurements on the benchmark environment rather than a universal latency law.

**4. Retrieval quality and biological task utility are different objectives.**

The classification experiments showed that some biological tasks retained very high Macro-F1 after substantial dimensionality reduction. In contrast, the vector-search experiment showed only 0.5547 Recall@10 at 256D relative to the exact 1280D neighbour set.

This does **not** mean that the 256D representation is biologically poor. It demonstrates that downstream task utility and preservation of the original embedding-space neighbourhood structure are distinct properties.

This distinction is central to the engineering objective: the appropriate dimensionality depends on the workload. A classification system, a similarity-search system, and a representation-store system may have different acceptable dimensions.

**5. Dimensionality should therefore be selected against workload-specific utility constraints.**

The experiments now support a three-part evaluation:

1. **Biological utility** — downstream classification performance.
2. **Representation cost** — storage, memory, data movement and dimension-scaled computation.
3. **Retrieval utility** — nearest-neighbour preservation and measured search performance.

Rather than assuming that the largest representation is always necessary, the engineering problem becomes selecting the smallest representation that satisfies the utility requirements of the actual workload.

### Benchmark reproducibility

The vector-search benchmark used FAISS 1.7.4, exact `IndexFlatIP` search, 10,000 database vectors, 718 queries, $K=10$, and five timing repeats. The reference neighbour set was generated using the exact 1280D representation.

The benchmark was run on the local experimental environment. Search timings and throughput are therefore hardware/software-specific measurements. Index-size reductions and compression ratios are representation-level quantities that scale predictably with vector count.


## CARE Task 1: enzyme-function generalization

The study is now being extended beyond remote homology using **CARE Task 1**, an enzyme-function benchmark from the CARE benchmark suite.

CARE Task 1 provides a substantially larger protein dataset and explicit enzyme-function labels, allowing the dimensionality-efficiency question to be tested on a different biological problem.

The downloaded training data contain:

- **184,529 protein records**
- **173,543 unique sequences**
- **4,936 EC-number labels**
- **7 EC1 classes**
- **69 EC2 classes**
- **243 EC3 classes**
- sequence lengths from **101 to 1,023 residues**
- mean sequence length of approximately **394 residues**
- identity clusters at 30%, 50%, 70%, and 90% sequence identity

### CARE Task 1 data inventory

The initial download notebook records the following Task 1 resources:

- `protein_train.csv`
- `30_protein_test.csv`
- `30-50_protein_test.csv`
- `price_protein_test.csv`
- `promiscuous_protein_test.csv`

The dataset inventory and schema were inspected before embedding generation. The primary sequence field is `Sequence`, with `EC number` as the fine-grained enzyme-function label and `EC1`, `EC2`, and `EC3` providing hierarchical labels.

### CARE embedding experiment

The next experiment generates **ESM-2 650M** embeddings using:

`facebook/esm2_t33_650M_UR50D`

with an original embedding dimension of **1280**.

The CARE embedding pipeline records:

- model name
- embedding dimension
- maximum sequence length
- batch size
- computation device
- random seed
- sequence and label metadata
- embedding-generation timing
- output shape and numerical validity

The initial dimensionality sweep will use:

$
D \in \{32,64,128,256,512,768,1024,1280\}.
$

The CARE experiments will first emphasize EC1 and EC3 classification, followed by more fine-grained EC-number analysis where class support and the official CARE evaluation protocol permit a meaningful comparison.

### Why CARE matters to the study

CARE adds an important cross-dataset test.

The remote-homology experiments ask whether dimensionality can be reduced while preserving protein-family/fold/superfamily discrimination.

CARE asks whether the same engineering behaviour appears for **enzyme-function classification**.

This lets the study distinguish between:

- behaviour that may be specific to one benchmark;
- behaviour that is consistent across different protein tasks;
- dimensions that provide robust utility across biological workloads.

The CARE identity-cluster metadata also provide an opportunity to investigate how representation requirements change as sequence similarity between training and evaluation examples changes.

### CARE experiment status

**Embedding generation is currently in progress.**

The experiment is intentionally kept separate from the large raw dataset and generated embedding artifacts. The repository will track the experimental methodology, compact results, and reproducibility information rather than committing the full CARE dataset or large embedding matrices.

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

- The remote-homology results focus on a specific protein embedding model and benchmark; CARE Task 1 is now being added as an independent cross-dataset validation.
- Results depend on the selected classifier, splits, and evaluation protocol.
- Dimensionality reduction can preserve variance without necessarily preserving task-relevant biological information.
- Accuracy alone is insufficient for imbalanced biological classification; Macro-F1 and balanced accuracy are therefore also reported.
- The engineering benchmark is based on a local environment and relatively small vector counts, so measured timings should not be generalized directly to production-scale infrastructure.
- The first-order cost model is dimension-scaled and is not a monetary cost model.
- The superfamily/fold holdout experiments expose difficult generalization regimes, including cases where labels are poorly represented or absent in training.
- Hierarchical shared-representation storage has not yet been experimentally validated.
- The exact vector-search benchmark uses a relatively small 10,000-vector database, so latency and throughput should not be generalized directly to production-scale vector stores.
- CARE embedding generation is currently in progress, so no CARE downstream performance or dimensionality results are reported yet.

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
- [x] Measure vector-index footprint
- [x] Benchmark exact vector search
- [ ] Produce empirical utility-vs-search-cost Pareto curves
- [ ] Define utility-threshold dimension selection

### Phase 3 — Cross-dataset biological validation

- [x] Identify CARE Task 1 as a second biological benchmark
- [x] Download and inventory CARE Task 1 data
- [x] Establish CARE Task 1 embedding pipeline
- [ ] Complete CARE ESM-2 embedding generation
- [ ] Validate embedding integrity and metadata alignment
- [ ] Evaluate EC1 classification across dimensions
- [ ] Evaluate EC3 classification across dimensions
- [ ] Evaluate fine-grained EC-number classification where appropriate
- [ ] Compare CARE dimensionality curves with remote homology
- [ ] Analyze identity-aware generalization

### Phase 4 — Additional reduction methods

Evaluate whether the same engineering behaviour appears across other protein tasks and datasets, including additional enzyme/protein classification benchmarks.

The objective is to determine whether the observed dimensionality trade-off is specific to remote homology or generalizes across biological representation tasks.

### Phase 6 — Hierarchical representations

- [ ] Construct biological group representations
- [ ] Model protein-specific residuals
- [ ] Compare flat and hierarchical storage
- [ ] Measure retrieval and downstream utility
- [ ] Quantify storage and compute savings

### Phase 7 — Production-scale evaluation

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

The repository contains the experimental foundation, biological dimensionality results, measured engineering benchmarks, and an exact vector-search benchmark. CARE Task 1 has now been added as the second biological validation dataset, with ESM-2 embedding generation currently in progress. The next step is to complete CARE embeddings and evaluate whether the dimensionality/utility trade-offs observed in remote homology generalize to enzyme-function classification.

## License

License and dataset-specific usage terms will be documented before redistributing any third-party data or derived artifacts.
