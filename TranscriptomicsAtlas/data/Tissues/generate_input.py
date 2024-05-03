import pandas as pd
from tqdm import tqdm


def get_only_valid_srr(tissue_name):
    tissue_srr_df = pd.read_csv(f"runs/RunInfo/{tissue_name}.csv")
    no_tumor_df = tissue_srr_df[tissue_srr_df['Tumor'] == 'no']
    human_only_df = no_tumor_df[no_tumor_df["ScientificName"] == "Homo sapiens"]
    public_only_df = human_only_df[human_only_df["Consent"] == "public"]
    valid_size_df = public_only_df[(public_only_df['size_MB'] >= 200) & (public_only_df['size_MB'] <= 30000)]
    valid_srr_df = valid_size_df

    return valid_srr_df


def sample_n_or_take_all(tissues_df, n):
    if len(tissues_df) < n:
        return tissues_df
    return tissues_df.sample(n=n, random_state=42).reset_index(drop=True)


tissue_names = ["adipose tissue", "breast cells", "endometrium", "endothelium", "epithelium", "fibroblasts",
                "heart muscle", "intestine", "kidney cells", "liver tissues", "lymphocytes", "lymphoid tissue",
                "nervous cells", "ovarian cells", "prostate tissue", "retina", "smooth muscle",
                "thyroid cells", "urinary bladder"]  # , "neutrophiles" , "fibrocytes"

inputs = []
for tissue_name in tqdm(tissue_names):
    tissues_df = get_only_valid_srr(tissue_name)
    sample_df = sample_n_or_take_all(tissues_df, 400)
    sample_df["tissue_name"] = tissue_name.replace(' ', '_')
    inputs.append(sample_df)

input_df = pd.concat(inputs).reset_index(drop=True)
input_df = input_df.rename(columns={"Run": "SRR_id"})
input_df.to_csv("experiment_input_df.csv")
