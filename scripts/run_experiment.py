#!/usr/bin/env python3
"""CLI script for running dataset experiments headlessly.

Usage:
    python scripts/run_experiment.py --dataset cnn_dailymail --num_samples 5
    python scripts/run_experiment.py --dataset xsum --num_samples 10 --include-llm
    python scripts/run_experiment.py --dataset cnn_dailymail --num_samples 50 --models t5 bart
"""

import argparse
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.experiment import experiment_runner


def main():
    parser = argparse.ArgumentParser(
        description="Run a dataset experiment for news summarization models."
    )
    parser.add_argument(
        "--dataset",
        choices=["cnn_dailymail", "xsum"],
        default="cnn_dailymail",
        help="Dataset to use (default: cnn_dailymail)",
    )
    parser.add_argument(
        "--num_samples", "-n",
        type=int,
        default=5,
        help="Number of samples to evaluate (default: 5)",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["t5", "bart", "pegasus"],
        help="Models to evaluate (default: t5 bart pegasus)",
    )
    parser.add_argument(
        "--include-llm",
        action="store_true",
        help="Include LLM model (requires GROQ_API_KEY, uses API calls)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=150,
        help="Maximum summary length in tokens (default: 150)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=30,
        help="Minimum summary length in tokens (default: 30)",
    )

    args = parser.parse_args()

    # Confirmation for large experiments
    if args.num_samples > 20:
        print(f"\n⚠️  Large experiment: {args.num_samples} samples × {len(args.models)} models")
        print(f"   Estimated time: {args.num_samples * len(args.models) * 15}–{args.num_samples * len(args.models) * 60}s on CPU")
        response = input("   Continue? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            return

    # Confirmation for LLM usage
    if args.include_llm:
        api_calls = args.num_samples
        print(f"\n⚠️  LLM mode enabled: This will make ~{api_calls} Groq API calls.")
        print(f"   Groq free tier limit: 1,000 requests/day for llama-3.3-70b.")
        response = input("   Continue? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            return

    # Progress callback
    def on_progress(progress: float, message: str):
        bar_len = 40
        filled = int(bar_len * progress)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\r  [{bar}] {progress*100:.0f}% — {message}", end="", flush=True)

    print(f"\n🔬 Starting experiment:")
    print(f"   Dataset:  {args.dataset}")
    print(f"   Samples:  {args.num_samples}")
    print(f"   Models:   {', '.join(args.models)}")
    print(f"   LLM:      {'Yes' if args.include_llm else 'No'}")
    print()

    try:
        results = experiment_runner.run_experiment(
            dataset=args.dataset,
            num_samples=args.num_samples,
            models=args.models,
            include_llm=args.include_llm,
            max_length=args.max_length,
            min_length=args.min_length,
            on_progress=on_progress,
        )
        print()  # Newline after progress bar
        print(f"\n✅ Experiment completed!")
        print(f"   ID:           {results['experiment_id']}")
        print(f"   Duration:     {results['execution_time_seconds']:.1f}s")
        print(f"   Output:       {results.get('output_path', 'N/A')}")

        # Print aggregate scores
        print(f"\n📊 Aggregate Scores:")
        print(f"   {'Model':<12} {'ROUGE-1':>10} {'ROUGE-2':>10} {'ROUGE-L':>10} {'Avg Time':>10}")
        print(f"   {'─'*12} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")
        
        for model_name, scores in results.get("aggregate_scores", {}).items():
            if scores.get("status") == "no_successful_runs":
                print(f"   {model_name:<12} {'FAILED':>10}")
                continue
            r1 = scores.get("avg_rouge_1")
            r2 = scores.get("avg_rouge_2")
            rl = scores.get("avg_rouge_l")
            t = scores.get("avg_generation_time")
            print(
                f"   {model_name:<12} "
                f"{r1:>10.4f} " if r1 is not None else f"   {model_name:<12} {'N/A':>10} ",
                end=""
            )
            print(f"{r2:>10.4f} " if r2 is not None else f"{'N/A':>10} ", end="")
            print(f"{rl:>10.4f} " if rl is not None else f"{'N/A':>10} ", end="")
            print(f"{t:>9.2f}s" if t is not None else f"{'N/A':>10}")

    except KeyboardInterrupt:
        print("\n\n⏹ Experiment interrupted.")
    except Exception as e:
        print(f"\n\n❌ Experiment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
