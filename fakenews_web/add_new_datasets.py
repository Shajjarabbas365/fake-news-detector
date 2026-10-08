import pandas as pd
import os

print("Processing the new datasets...\n")

new_data_frames = []

# 1. Bharat Fake News Kosh (Excel or CSV)
excel_files = [
    "bharatfakenewskosh (3).xlsx",
    "bharatfakenewskosh.xlsx",
    "bharatfakenewskosh.csv",
]

for fname in excel_files:
    if os.path.exists(fname):
        try:
            if fname.endswith(".xlsx"):
                df1 = pd.read_excel(fname)
            else:
                df1 = pd.read_csv(fname)

            df1_clean = pd.DataFrame()

            # Use the English translation of the news article
            df1_clean["text"] = df1["Eng_Trans_News_Body"].fillna(
                df1["Eng_Trans_Statement"]
            )

            # TRUE = Real (1), otherwise = Fake (0)
            df1_clean["label"] = df1["Label"].apply(
                lambda x: 1 if str(x).strip().upper() == "TRUE" else 0
            )

            new_data_frames.append(df1_clean)
            print(f"✅ Bharat Fake News dataset loaded successfully ({fname}).")
            break

        except Exception as e:
            print(f"❌ Bharat Fake News Error: {e}")


# 2. Clickbait Dataset
if os.path.exists("clickbait_data.csv"):
    try:
        df2 = pd.read_csv("clickbait_data.csv")

        df2_clean = pd.DataFrame()
        df2_clean["text"] = df2["headline"]

        # Clickbait = Fake (0), Non-clickbait = Real (1)
        df2_clean["label"] = df2["clickbait"].apply(
            lambda x: 0 if x == 1 else 1
        )

        new_data_frames.append(df2_clean)
        print("✅ Clickbait dataset loaded successfully.")

    except Exception as e:
        print(f"❌ Clickbait Dataset Error: {e}")


# 3. Kaggle Train / General News
if os.path.exists("train.csv"):
    try:
        df3 = pd.read_csv("train.csv")

        df3_clean = pd.DataFrame()

        # Use the article text, or the title if text is missing
        df3_clean["text"] = df3["text"].fillna(df3["title"])

        # Label "news" as Real (1), everything else as Fake (0)
        df3_clean["label"] = df3["label"].apply(
            lambda x: 1 if str(x).strip().lower() == "news" else 0
        )

        new_data_frames.append(df3_clean)
        print("✅ Kaggle Train News dataset loaded successfully.")

    except Exception as e:
        print(f"❌ Kaggle Train Error: {e}")


# 4. Indian Fake News
indian_files = [
    "Indian Fake News.csv",
    "Indian_Fake_News.csv",
    "indianfakenews.csv",
]

for fname in indian_files:
    if os.path.exists(fname):
        try:
            df4 = pd.read_csv(fname)

            df4_clean = pd.DataFrame()
            df4_clean["text"] = df4["text"]

            # REAL = 1, otherwise = Fake (0)
            df4_clean["label"] = df4["label"].apply(
                lambda x: 1 if str(x).strip().upper() == "REAL" else 0
            )

            new_data_frames.append(df4_clean)
            print(f"✅ Indian Fake News dataset loaded successfully ({fname}).")
            break

        except Exception as e:
            print(f"❌ Indian Fake News Error: {e}")


# 5. Sarcasm Headlines Dataset
json_files = [
    "Sarcasm_Headlines_Dataset.json",
    "Sarcasm_Headlines_Dataset_v2.json",
]

for fname in json_files:
    if os.path.exists(fname):
        try:
            df5 = pd.read_json(fname, lines=True)

            df5_clean = pd.DataFrame()
            df5_clean["text"] = df5["headline"]

            # Sarcastic headlines are treated as Fake/Satire (0)
            df5_clean["label"] = df5["is_sarcastic"].apply(
                lambda x: 0 if x == 1 else 1
            )

            new_data_frames.append(df5_clean)
            print(f"✅ Sarcasm Headlines dataset loaded successfully ({fname}).")

        except Exception as e:
            print(f"❌ Sarcasm Headlines Error ({fname}): {e}")


# 6. Onion Or Not
if os.path.exists("OnionOrNot.csv"):
    try:
        df6 = pd.read_csv("OnionOrNot.csv")

        df6_clean = pd.DataFrame()
        df6_clean["text"] = df6["text"]

        # Onion = Satire/Fake (0), Normal = Real (1)
        df6_clean["label"] = df6["label"].apply(
            lambda x: 0 if x == 1 else 1
        )

        new_data_frames.append(df6_clean)
        print("✅ Onion Or Not dataset loaded successfully.")

    except Exception as e:
        print(f"❌ Onion Or Not Error: {e}")


# 7. PHEME Rumor Dataset
if os.path.exists("PHEME.csv"):
    try:
        df7 = pd.read_csv("PHEME.csv")

        df7_clean = pd.DataFrame()
        df7_clean["text"] = df7["text"]

        # Rumor = Fake (0), Non-rumor = Real (1)
        df7_clean["label"] = df7["is_rumor"].apply(
            lambda x: 0 if x == 1 else 1
        )

        new_data_frames.append(df7_clean)
        print("✅ PHEME Rumor dataset loaded successfully.")

    except Exception as e:
        print(f"❌ PHEME Rumor Dataset Error: {e}")


# 8. The Onion Breaking News
onion_files = [
    "The Onions Breaking News.csv",
    "The_Onions_Breaking_News.csv",
]

for fname in onion_files:
    if os.path.exists(fname):
        try:
            df8 = pd.read_csv(fname)

            df8_clean = pd.DataFrame()

            # Use the article content, or fall back to the title
            df8_clean["text"] = df8["Content"].fillna(df8["Title"])

            # All Onion articles are satire (Fake = 0)
            df8_clean["label"] = 0

            new_data_frames.append(df8_clean)
            print(f"✅ The Onion Breaking News dataset loaded successfully ({fname}).")
            break

        except Exception as e:
            print(f"❌ The Onion Breaking News Error: {e}")


# Combine all processed datasets
if len(new_data_frames) > 0:

    combined_new_data = pd.concat(
        new_data_frames,
        ignore_index=True,
    )

    combined_new_data = combined_new_data.dropna(
        subset=["text", "label"]
    )

    print(f"\nTotal new articles extracted: {len(combined_new_data)}")

    # Append the new data to the existing master dataset
    if os.path.exists("master_combined_news.csv"):

        old_master = pd.read_csv("master_combined_news.csv")

        final_master = pd.concat(
            [old_master, combined_new_data],
            ignore_index=True,
        )

        final_master.to_csv(
            "master_combined_news.csv",
            index=False,
        )

        print(
            f"🎉 The new data has been added to the master dataset! "
            f"Total articles: {len(final_master)}"
        )

    else:
        combined_new_data.to_csv(
            "master_combined_news.csv",
            index=False,
        )

        print("🎉 'master_combined_news.csv' has been created successfully!")

else:
    print(
        "\n⚠️ No datasets could be loaded. "
        "Please check that the files are available in the project folder."
    )