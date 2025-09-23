#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { PromptRegistryMCP } from "./prompt-registry-mcp.js";

async function main() {
  const transport = new StdioServerTransport();
  const server = new Server(
    {
      name: "prompt-registry-mcp",
      version: "0.1.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  const promptRegistry = new PromptRegistryMCP();

  // List available tools
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: "list_prompts",
          description: "List all available prompts",
          inputSchema: {
            type: "object",
            properties: {
              package_name: {
                type: "string",
                description: "Optional package name to filter by",
              },
              limit: {
                type: "number",
                description: "Maximum number of results",
                default: 10,
              },
            },
          },
        },
        {
          name: "get_prompt",
          description: "Get a specific prompt by ID",
          inputSchema: {
            type: "object",
            properties: {
              prompt_id: {
                type: "string",
                description: "ID of the prompt to retrieve",
              },
              version: {
                type: "string",
                description: "Specific version (defaults to latest)",
              },
              package_name: {
                type: "string",
                description: "Specific package to search in",
              },
            },
            required: ["prompt_id"],
          },
        },
        {
          name: "search_prompts",
          description: "Search for prompts by query",
          inputSchema: {
            type: "object",
            properties: {
              query: {
                type: "string",
                description: "Search query",
              },
              tags: {
                type: "array",
                items: { type: "string" },
                description: "Filter by tags",
              },
              limit: {
                type: "number",
                description: "Maximum number of results",
                default: 10,
              },
            },
            required: ["query"],
          },
        },
        {
          name: "preprocess_input",
          description: "Preprocess user input to improve prompt effectiveness",
          inputSchema: {
            type: "object",
            properties: {
              input_text: {
                type: "string",
                description: "Original user input",
              },
              transformations: {
                type: "array",
                items: { type: "string" },
                description: "Transformations to apply",
              },
              prompt_id: {
                type: "string",
                description:
                  "Optional prompt ID for context-specific preprocessing",
              },
            },
            required: ["input_text"],
          },
        },
        {
          name: "grade_prompt_execution",
          description: "Grade a prompt execution for quality and success",
          inputSchema: {
            type: "object",
            properties: {
              prompt_id: {
                type: "string",
                description: "ID of the prompt that was used",
              },
              user_input: {
                type: "string",
                description: "Original user input",
              },
              ai_response: {
                type: "string",
                description: "AI response to grade",
              },
              expected_outcome: {
                type: "string",
                description: "Expected outcome (optional)",
              },
              grader_type: {
                type: "string",
                enum: ["llm", "rule_based"],
                description: "Type of grader to use",
                default: "rule_based",
              },
            },
            required: ["prompt_id", "user_input", "ai_response"],
          },
        },
        {
          name: "get_prompt_analytics",
          description: "Get analytics for a specific prompt",
          inputSchema: {
            type: "object",
            properties: {
              prompt_id: {
                type: "string",
                description: "ID of the prompt to get analytics for",
              },
            },
            required: ["prompt_id"],
          },
        },
        {
          name: "get_best_prompt",
          description: "Get the best prompt for a given input",
          inputSchema: {
            type: "object",
            properties: {
              user_input: {
                type: "string",
                description: "User input to find best prompt for",
              },
              context: {
                type: "object",
                description: "Additional context for prompt selection",
              },
            },
            required: ["user_input"],
          },
        },
        {
          name: "track_prompt_usage",
          description: "Track usage of a prompt",
          inputSchema: {
            type: "object",
            properties: {
              prompt_id: {
                type: "string",
                description: "ID of the prompt that was used",
              },
              user_input: {
                type: "string",
                description: "User input",
              },
              response_time: {
                type: "number",
                description: "Response time in seconds",
              },
              token_usage: {
                type: "number",
                description: "Number of tokens used",
              },
            },
            required: ["prompt_id"],
          },
        },
      ] as Tool[],
    };
  });

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case "list_prompts":
          return await promptRegistry.listPrompts(args);

        case "get_prompt":
          return await promptRegistry.getPrompt(args);

        case "search_prompts":
          return await promptRegistry.searchPrompts(args);

        case "preprocess_input":
          return await promptRegistry.preprocessInput(args);

        case "grade_prompt_execution":
          return await promptRegistry.gradePromptExecution(args);

        case "get_prompt_analytics":
          return await promptRegistry.getPromptAnalytics(args);

        case "get_best_prompt":
          return await promptRegistry.getBestPrompt(args);

        case "track_prompt_usage":
          return await promptRegistry.trackPromptUsage(args);

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error: ${
              error instanceof Error ? error.message : String(error)
            }`,
          },
        ],
        isError: true,
      };
    }
  });

  await server.connect(transport);
  console.error("Prompt Registry MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
