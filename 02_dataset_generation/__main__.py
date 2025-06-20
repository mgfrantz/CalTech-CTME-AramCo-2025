import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import structlog

# Configure structlog BEFORE importing other modules
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger(__name__)

from .main_graph import graph as main_graph
from .database_executor import DatabaseExecutor


async def main():
    """
    Main function to run the complete database generation and validation pipeline.
    """
    logger.info("Dataset generation pipeline starting")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate and validate synthetic databases")
    parser.add_argument(
        "--num-databases", 
        type=int, 
        default=2, 
        help="Number of databases to generate (default: 2)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for results (default: output)"
    )
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
        
    logger.info("Starting dataset generation", 
                num_databases=args.num_databases,
                output_dir=str(output_dir))
    
    # Check if state.json already exists
    state_json_path = output_dir / "state.json"
    if state_json_path.exists():
        logger.info("Loading existing state from file", state_path=str(state_json_path))
        with open(state_json_path, "r") as f:
            state = json.load(f)
    else:
        # Run the main graph to generate databases
        state = await main_graph.ainvoke({"num_requests": args.num_databases})
        
        logger.info("Database generation complete", 
                    databases_generated=len(state['databases']))
        
        # Save state
        with open(state_json_path, "w") as f:
            json.dump(state, f, indent=4)
        
        logger.info("State saved", state_path=str(state_json_path))
    
    logger.info("Processing databases", 
                databases_count=len(state['databases']))
    
    # Run the database executor - save databases in db subfolder for organization
    db_folder = output_dir / "db"
    executor = DatabaseExecutor(db_folder=str(db_folder))
    results = executor.process_main_graph_output(state)
    
    # Save dataset
    dataset_path = output_dir / "validated_dataset.parquet"
    executor.save_dataset(results, str(dataset_path))
    
    logger.info("Dataset generation pipeline complete")


if __name__ == "__main__":
    asyncio.run(main())
