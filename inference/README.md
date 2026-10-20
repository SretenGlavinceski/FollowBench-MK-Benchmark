# Inference

`followbench_mk_inference.ipynb` generated all 800 responses on Google Colab.

## Settings

| Setting | Value |
|---|---|
| Hardware | NVIDIA Tesla T4 (16 GB) |
| Libraries | `transformers` 5.18.0, `accelerate`, `bitsandbytes` |
| Quantization | 4-bit NF4, double quantization, float16 compute |
| Decoding | greedy (`do_sample=False`), seed 42 |
| Length limit | 2,048 new tokens; a response that reaches it is marked `truncated` |
| Prompt format | the model's own chat template, one user message, no system prompt |
| Thinking | off for Qwen3.5 9B and Gemma 4 12B (`enable_thinking=False`) |

## How to run it

1. Open the notebook in Google Colab with a T4 GPU.
2. Copy `data/prompts/followbench_en.jsonl` and `followbench_mk.jsonl` to `MyDrive/followbench_mk/` in Google Drive.
3. Add a Hugging Face token to Colab secrets as `HF_TOKEN` (needed for Llama 3.1).
4. In section 2, keep one model in `MODELS_TO_RUN`. We ran each model from a different account at the same time.
5. Run all cells. Each answer is saved to Drive as soon as it is produced; if the session stops, running again continues where it stopped.

The outputs, `results/<model>__<lang>.jsonl`, are the files in `data/responses/raw/`.
