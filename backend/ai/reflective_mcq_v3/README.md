# Iteration 3 Live Reflective MCQ RAG Service

This handover contains the AI component for generating one live reflective workplace MCQ when a user supplies a relevant custom skill.

## Runtime workflow

1. Validate the custom skill as untrusted input.
2. Use local hybrid retrieval to find up to three relevant catalogue skills.
3. Retrieve two validated Version 3 scenarios for the same role and difficulty.
4. Ground Gemini in the exact custom skill and retrieved evidence.
5. Validate the generated JSON locally.
6. Retry once when validation fails.
7. Return the matching Version 2 static fallback when live generation remains unavailable.

## Product behaviour

A custom-skill practice session can serve:

- four pre-generated Version 3 questions;
- one live RAG-grounded Gemini question.

If live generation fails, the fifth question comes from the Version 2 fallback pool.

The activities are reflective and ungraded. No option is marked correct or incorrect.

## Main files

- `live_mcq_rag_service.py`: standalone retrieval, generation, validation and fallback service
- `models/live_mcq_hybrid_semantic_retriever_v2_2.joblib`: saved retrieval index
- `data/reflective_mcq_scenario_pool_v3_final.json`: 324 validated static questions
- `data/reflective_mcq_scenario_pool_v2_fallback.json`: 81 fallback questions
- `live_mcq_generation_contract.json`: request and response contract
- `reports/`: evaluation and validation evidence
- `MODEL_DEPLOYMENT.md`: deployment instructions

## Evaluation summary

- 324 Version 3 static questions validated
- 27 roles
- 3 difficulty levels
- 4 static questions per role and difficulty combination
- 6/6 balanced live-generation tests passed
- 6/6 accepted on the first attempt
- mean live latency: 3.77 seconds
- p95 live latency: 3.92 seconds
- 4/4 custom-skill security tests passed
- forced static fallback test passed
- zero exact or near-duplicate situations in the live evaluation sample

The six-question live evaluation is integration evidence and should not be described as proof of universal content quality.
