import os
import re
import tensorflow as tf
from transformers import TFAutoModelForSeq2SeqLM, AutoTokenizer
from vtt_to_srt.vtt_to_srt import ConvertFile


def extract_text_from_vtt(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    # Remove VTT header and metadata
    content = re.sub(r"WEBVTT.*\n", "", content)
    # Remove all the timestamps
    content = re.sub(
        r"\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}", "", content
    )
    # Remove any extra lines and whitespace
    content = re.sub(r"\n\n+", "\n", content).strip()
    captions = re.sub(r">>", "", content)

    return captions


def combine_sentences_into_blocks(sentences, block_size=4):
    combined_blocks = []
    current_block = []

    for i, sentence in enumerate(sentences):
        current_block.append(sentence)

        if (i + 1) % block_size == 0:
            combined_blocks.append(" ".join(current_block))
            current_block = []

    # If there are remaining sentences that haven't formed a full block
    if current_block:
        combined_blocks.append(" ".join(current_block))

    return combined_blocks


def generate_questions_answers(text, model, tokenizer, limit=None):
    sentences = text.split(". ")
    text_blocks = combine_sentences_into_blocks(sentences)
    qa_pairs = []

    for i, sentence in enumerate(text_blocks):
        if sentence:
            input_text = f"generate question: {sentence}"
            input_ids = tokenizer.encode(input_text, return_tensors="tf")
            outputs = model.generate(input_ids)
            question = tokenizer.decode(outputs[0], skip_special_tokens=True)

            qa_pairs.append(
                {"context": sentence, "question": question, "answer": sentence}
            )

            if limit is not None and i + 1 >= limit:
                break

    return qa_pairs


def write_processed_captions(raw_path: str, text: str):
    processed_path = raw_path.replace("raw", "processed")
    processed_path = processed_path.replace(".vtt", ".txt")
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    with open(processed_path, "w") as processed:
        processed.write(text)


def convert_to_srt(raw_path: str):
    convert_file = ConvertFile(raw_path, "utf-8")
    convert_file.convert()


# Load pre-trained T5 model and tokenizer
model_name = "t5-small"  # You can use other T5 models as well
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = TFAutoModelForSeq2SeqLM.from_pretrained(model_name)

# Extract text from captions file
srt_file_path = "data/raw/2023/january/01_24_23_board_meeting.vtt"
captions_text = extract_text_from_vtt(srt_file_path)
write_processed_captions(srt_file_path, captions_text)
convert_to_srt(srt_file_path)

# # Generate QA pairs
# qa_pairs = generate_questions_answers(captions_text, model, tokenizer, 5)

# # Print QA pairs
# for qa in qa_pairs:
#     print(f"Context: {qa['context']}")
#     print(f"Question: {qa['question']}")
#     print(f"Answer: {qa['answer']}\n")
