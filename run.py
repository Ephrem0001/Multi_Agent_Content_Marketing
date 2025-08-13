import argparse
import os
from dotenv import load_dotenv  # type: ignore

from utils.io_utils import create_output_dir, save_json
from orchestration.main_graph import build_graph


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Multi-Agent Content Marketing CLI")
    parser.add_argument("--topic", required=True, help="Product or topic to generate content for")
    parser.add_argument("--no-image", action="store_true", help="Skip image generation")
    parser.add_argument("--output-root", default=os.getenv("OUTPUT_ROOT", "outputs"), help="Root output directory")
    args = parser.parse_args()

    output_dir = create_output_dir(args.topic, base_output_root=args.output_root)
    include_image = not args.no_image

    app = build_graph(include_image=include_image)
    # Initial state
    state = {"topic": args.topic, "output_dir": output_dir}
    final_state = app.invoke(state)

    save_json(os.path.join(output_dir, "final_state.json"), final_state)
    print(f"Saved outputs to: {output_dir}")


if __name__ == "__main__":
    main()


