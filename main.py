from pcd_rlcd.schema import StructuredSchema
from pcd_rlcd.engine import run_parallel_generation

# 1. Define schema
schema_definition = {
    "fraud_risk": {
        "type": "enum",
        "choices": ["LOW", "ELEVATED", "SUSPICIOUS", "CRITICAL"],
        "description": "Risk assessment tier for incoming transaction",
    },
    "block_account": {
        "type": "boolean",
        "description": "Whether immediate account restriction is required",
    },
    "recommended_action": {
        "type": "enum",
        "choices": ["ALLOW", "STEP_UP_2FA", "TEMPORARY_HOLD", "TERMINATE_SESSION"],
        "description": "Immediate mitigation action",
    },
}


def main():
    schema = StructuredSchema(schema_definition)

    # 2. Provide context
    context = """
    User ID: usr_9921
    Location: Lagos, Nigeria (usual: Seattle, USA)
    Device: Unknown Linux Chromium browser
    Action: Wire transfer $49,500 to offshore escrow
    Prior velocity: 0 transfers in 90 days
    """

    # 3. Execute parallel generation
    result = run_parallel_generation(context, schema)

    print(f"Elapsed Time: {result['elapsed_ms']} ms")
    print(f"Sequential Passes: {result['sequential_forward_passes']}")
    print(f"Parsed JSON: {result['parsed_json']}")


if __name__ == "__main__":
    main()
