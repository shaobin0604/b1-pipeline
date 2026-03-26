from src.pipeline.fetch_pipeline import run_fetch_pipeline
from src.pipeline.preprocess_pipeline import run_preprocess_pipeline
from src.pipeline.preselect_pipeline import run_preselect_pipeline
from src.pipeline.chart_pipeline import run_chart_pipeline
from src.pipeline.review_pipeline import run_review_pipeline


def run_full_pipeline(pick_date: str, skip_fetch: bool = False):
    if not skip_fetch:
        run_fetch_pipeline()
    run_preprocess_pipeline()
    run_preselect_pipeline(pick_date)
    run_chart_pipeline(pick_date)
    run_review_pipeline(pick_date)
