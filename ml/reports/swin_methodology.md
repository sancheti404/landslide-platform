# Swin Transformer Satellite / Visual Landslide-Risk Methodology

**Uttarakhand Landslide Intelligence Platform — Visual Branch (Step 39)**  
**Authoritative Architectural Component**: Satellite / Visual Risk Branch  
**Target Output**: $P(\text{satellite visual evidence indicates landslide})$

---

## 1. Executive Summary & Architectural Role

The Uttarakhand Landslide Intelligence Platform employs a decoupled tri-branch machine-learning architecture:
1. **XGBoost Branch**: Evaluates static terrain and geo-environmental susceptibility (elevation, slope, aspect, curvature, TWI, baseline LULC, precipitation normals).
2. **Swin Transformer Branch (Current Component)**: Evaluates high-resolution optical satellite imagery (Sentinel-2 SR) for visual indicators of slope instability, exposed soil/scarps, vegetative denudation, and local geomorphological disturbance.
3. **Temporal Fusion Transformer (TFT) Branch**: Evaluates dynamic triggering factors (short-term antecedent precipitation, monsoon anomalies).
4. **Multimodal Late Fusion (Downstream)**: Fuses continuous probability outputs from all three branches into a final operational landslide risk prediction.

> [!IMPORTANT]
> The Swin Transformer branch outputs a continuous calibrated probability termed **`satellite_risk_probability`** ($P(\text{satellite visual evidence indicates landslide})$). It is **not** claimed that a single optical RGB snapshot establishes definitive ground truth for active slide mass movement; rather, it quantifies the degree of surface disturbance, scarp signature, and optical susceptibility visible from orbit.

---

## 2. Sentinel-2 Data Source & Acquisition

- **Earth Engine Asset**: `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2 Level-2A Surface Reflectance Harmonized).
- **Temporal Window**: `2023-01-01` to `2024-01-01` (full annual cycle, matching the Step 34E NDVI feature extraction baseline).
- **Scene-Level Cloud Filter**: Scenes restricted to `CLOUDY_PIXEL_PERCENTAGE < 30%`.
- **Pixel-Level Cloud / Shadow Masking**: Filtered using the Sentinel-2 Scene Classification Layer (SCL) to remove:
  - Class 3: Cloud shadow
  - Class 8: Cloud medium probability
  - Class 9: Cloud high probability
  - Class 10: Thin cirrus
- **Temporal Aggregation**: Per-pixel **median composite** computed across cloud-masked observations over the Uttarakhand geographic envelope (`77.5°E–81.1°E`, `28.7°N–31.5°N`). This produces a cloud-free, shadow-suppressed, temporally stable surface reflectance representation.
- **Spectral Bands**:
  - Band 4: Red (central wavelength 665 nm, native 10 m resolution)
  - Band 3: Green (central wavelength 560 nm, native 10 m resolution)
  - Band 2: Blue (central wavelength 490 nm, native 10 m resolution)

---

## 3. Image Patch Extraction & Normalization

- **Spatial Extent**: Fixed square patches of $128 \times 128$ pixels centered precisely at the geographic coordinates of each sample point.
- **Physical Ground Footprint**:
  $$\text{Ground Footprint} = 128\text{ pixels} \times 10\text{ meters/pixel} = 1,280\text{ meters} \times 1,280\text{ meters} \approx 1.28\text{ km} \times 1.28\text{ km}$$
  Total spatial coverage per patch: $\approx 1.64\text{ km}^2$.
- **Radiometric Normalization**:
  - Sentinel-2 Level-2A surface reflectance values (0 to 10,000 scale factor, where 10,000 = 1.0) are scaled to $[0, 3000]$ (corresponding to $0.0 - 0.30$ surface reflectance, standard for vegetation and terrestrial soil) and converted to 8-bit RGB.
  - Normalization for Swin Transformer uses ImageNet RGB channel statistics:
    $$\mu = [0.485, 0.456, 0.406], \quad \sigma = [0.229, 0.224, 0.225]$$
- **Label Independence**: Preprocessing and patch generation are completely agnostic to the binary landslide label.

---

## 4. Dataset Alignment & Split Integrity

Every image patch strictly adheres to the authoritative master dataset and metadata:
- **Total Master Samples**: 11,046 samples (5,523 positive, 5,523 negative; perfectly balanced 50/50).
- **Split Partitions**:
  - **Training Split (`train_metadata.csv`)**: 8,836 samples (4,418 positive, 4,418 negative).
    - Internal Train Subsplit: 7,068 samples (80% stratified, random seed 42).
    - Internal Validation Subsplit: 1,768 samples (20% stratified, random seed 42).
  - **Held-Out Test Split (`test_metadata.csv`)**: 2,210 samples (1,105 positive, 1,105 negative).
- **Strict Quarantine**: The 2,210 held-out test samples are never accessed during feature selection, backbone freezing/unfreezing, hyperparameter tuning, or early stopping.
- **Sample Traceability**: Each patch is named `<sample_id>.png` and cataloged in `ml/data/processed/patches/manifest.csv`.

---

## 5. Model Architecture & Transfer Learning

- **Architecture**: Swin Transformer Tiny (`swin_t` via torchvision/PyTorch).
  - Employs Hierarchical Shifted Windows (Window Multi-Head Self-Attention, W-MSA and SW-MSA).
  - Patch resolution: $4 \times 4$ pixels; window size: $7 \times 7$.
  - Feature embedding dimension: $C = 96$.
  - Total parameters: $\approx 27.5$ million.
- **Transfer Learning Protocol**:
  - Initialized with ImageNet-1K pretrained weights (`Swin_T_Weights.DEFAULT`).
  - Classification head replaced: original 1000-class linear head replaced with `nn.Dropout(p=0.3)` followed by `nn.Linear(768, 1)`.
- **Two-Phase Training**:
  1. **Phase 1 (Linear Probing)**: Backbone frozen entirely. Only the binary classification head is trained for 3 epochs with learning rate $1 \times 10^{-3}$ using the AdamW optimizer.
  2. **Phase 2 (Controlled Fine-Tuning)**: Later stages (Stage 3 and 4 blocks) are unfrozen while early patch partition and stem layers remain frozen. Trained with learning rate $5 \times 10^{-5}$ regulated by a Cosine Annealing learning rate schedule (`eta_min=1e-6`).
- **Loss Function**: Binary Cross-Entropy with Logits (`nn.BCEWithLogitsLoss()`). Because the dataset is balanced, no artificial positive class weighting is applied.
- **Early Stopping**: Monitored exclusively on the internal validation set ROC-AUC with a patience of 4 epochs.

---

## 6. Data Augmentation Protocol

Spatial invariance is enforced during training without introducing non-physical radiometric artifacts:
- **Augmentations Applied to Training Split Only**:
  - `RandomHorizontalFlip(p=0.5)`
  - `RandomVerticalFlip(p=0.5)`
  - `RandomRotation(degrees=[0, 90, 180, 270])` (discrete orthogonal rotations preserving satellite viewing geometry)
- **Validation and Test Splits**:
  - Deterministic evaluation pipeline only (bilinear resize to $224 \times 224 \times 3$, normalization with ImageNet mean/std).

---

## 7. Spatial Leakage Analysis & Footprint Overlap

Because the sample coordinates were spatially sampled across the complex terrain of Uttarakhand, satellite patches with a $1.28\text{ km} \times 1.28\text{ km}$ footprint can overlap if neighbor samples are closer than $1,280\text{ meters}$.

A rigorous 3D Earth-Centered Earth-Fixed (ECEF) spatial index query (`cKDTree`) between splits revealed:

| Comparison | Source Samples | Target Samples | Overlapping Footprints (<1.28 km) | Overlap % | Min Dist (m) | Median Dist (m) | Mean Dist (m) |
|---|---|---|---|---|---|---|---|
| **Validation $\rightarrow$ Nearest Train** | 1,768 | 7,068 | 1,008 | 57.01% | 0.0 m | 1,058.8 m | 1,269.7 m |
| **Test $\rightarrow$ Nearest Train** | 2,210 | 7,068 | 1,339 | 60.59% | 0.0 m | 980.6 m | 1,191.5 m |
| **Test $\rightarrow$ Nearest Train+Val** | 2,210 | 8,836 | 1,469 | 66.47% | 0.0 m | 844.6 m | 1,039.0 m |

### Scientific Implications of Spatial Overlap:
1. **Clustered Landslide Events**: Landslide inventories naturally exhibit spatial clustering along valley corridors, fault zones, and highway cuts (e.g., Alaknanda and Bhagirathi valleys).
2. **Footprint Sharing**: Approximately $66.5\%$ of test patches share some optical background territory with a training sample patch.
3. **Quarantine Compliance**: While physical footprint overlap exists in nature, the split definitions in `train_metadata.csv` and `test_metadata.csv` were kept **strictly intact** as mandated by project requirements.
4. **Experimental Limitation**: In future iterations, spatial blocking or spatial buffer exclusion (e.g., spatial k-fold cross-validation with $>1.5\text{ km}$ buffer zones) could be tested to evaluate out-of-region spatial generalization.

---

## 8. Artifacts & Reproducibility Matrix

The Swin Transformer pipeline outputs the following validated artifacts:

| Category | Artifact Path | Description |
|---|---|---|
| **Model Weights** | `ml/models/swin/swin_transformer_best.pth` | Best validation ROC-AUC checkpoint |
| **Model Config** | `ml/models/swin/swin_transformer_config.json` | Architecture & training configuration |
| **Labels** | `ml/models/swin/swin_label_mapping.json` | Binary class label mapping |
| **Test Predictions** | `ml/reports/model_evaluation/swin_test_predictions.csv` | Critical prediction output for multimodal fusion |
| **Val Predictions** | `ml/reports/model_evaluation/swin_validation_predictions.csv` | Validation predictions for OOF fusion alignment |
| **Test Metrics** | `ml/reports/model_evaluation/swin_test_metrics.csv` | 14 test performance metrics |
| **Training History** | `ml/reports/model_evaluation/swin_training_history.csv` | Epoch-by-epoch loss, AUC, accuracy, learning rate |
| **Spatial Leakage** | `ml/reports/analysis/swin_spatial_leakage_analysis.csv` | Footprint overlap and distance distribution table |
| **Visualizations** | `ml/reports/figures/swin_confusion_matrix.png` | Test confusion matrix heatmap |
| **Visualizations** | `ml/reports/figures/swin_roc_curve.png` | Test ROC curve with AUC |
| **Visualizations** | `ml/reports/figures/swin_precision_recall_curve.png` | Test PR curve with PR-AUC |
| **Visualizations** | `ml/reports/figures/swin_training_history.png` | Dual-panel loss and metric curves |
| **Visualizations** | `ml/reports/figures/swin_spatial_distance_distribution.png` | Nearest-neighbor distance histogram |
