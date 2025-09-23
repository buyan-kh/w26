import { readFileSync, existsSync } from "fs";
import { join } from "path";
import { parse as parseYaml } from "yaml";
import OpenAI from "openai";

interface Prompt {
  id: string;
  name: string;
  content: string;
  version: string;
  description?: string;
  tags: string[];
  author?: string;
  usage_count: number;
  success_rate?: number;
}

interface PromptPackage {
  name: string;
  version: string;
  description?: string;
  author?: string;
  prompts: Prompt[];
}

interface PromptGrade {
  prompt_id: string;
  user_input: string;
  ai_response: string;
  overall_score: number;
  accuracy: number;
  helpfulness: number;
  completeness: number;
  clarity: number;
  reasoning: string;
  grader_type: string;
  is_successful: boolean;
}

interface ProcessedInput {
  original_input: string;
  processed_input: string;
  transformations_applied: string[];
  confidence: number;
}

interface PromptAnalytics {
  prompt_id: string;
  total_uses: number;
  successful_uses: number;
  failed_uses: number;
  success_rate: number;
  average_score: number;
  common_failures: string[];
  improvement_suggestions: string[];
  last_updated: string;
}

export class PromptRegistryMCP {
  private registryPath: string;
  private packages: Map<string, PromptPackage> = new Map();
  private analytics: Map<string, PromptAnalytics> = new Map();
  private openai?: OpenAI;

  constructor() {
    this.registryPath = process.env.PROMPT_REGISTRY_PATH || "./prompts";
    this.loadPackages();
    this.loadAnalytics();

    // Initialize OpenAI if API key is available
    if (process.env.OPENAI_API_KEY) {
      this.openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
      });
    }
  }

  private loadPackages(): void {
    try {
      const packagesDir = join(this.registryPath, "packages");
      if (!existsSync(packagesDir)) {
        return;
      }

      // Load package metadata
      const packageFiles = require("fs")
        .readdirSync(packagesDir, { withFileTypes: true })
        .filter((dirent: any) => dirent.isDirectory())
        .map((dirent: any) => dirent.name);

      for (const packageName of packageFiles) {
        const packagePath = join(packagesDir, packageName);
        const metadataFile = join(packagePath, "prompt-registry.json");

        if (existsSync(metadataFile)) {
          const metadata = JSON.parse(readFileSync(metadataFile, "utf-8"));
          const prompts: Prompt[] = [];

          // Load prompts from YAML files
          const promptsDir = join(packagePath, "prompts");
          if (existsSync(promptsDir)) {
            const promptFiles = require("fs")
              .readdirSync(promptsDir, { recursive: true })
              .filter(
                (file: string) =>
                  file.endsWith(".yaml") || file.endsWith(".yml")
              );

            for (const promptFile of promptFiles) {
              const promptPath = join(promptsDir, promptFile);
              const promptData = parseYaml(readFileSync(promptPath, "utf-8"));
              prompts.push({
                id: promptData.id,
                name: promptData.name,
                content: promptData.content,
                version: promptData.version || "1.0.0",
                description: promptData.description,
                tags: promptData.tags || [],
                author: promptData.author,
                usage_count: promptData.usage_count || 0,
                success_rate: promptData.success_rate,
              });
            }
          }

          const packageData: PromptPackage = {
            name: metadata.name || packageName,
            version: metadata.version || "1.0.0",
            description: metadata.description,
            author: metadata.author,
            prompts,
          };

          this.packages.set(packageData.name, packageData);
        }
      }
    } catch (error) {
      console.error("Error loading packages:", error);
    }
  }

  private loadAnalytics(): void {
    try {
      const analyticsDir = join(this.registryPath, "analytics");
      if (!existsSync(analyticsDir)) {
        return;
      }

      const analyticsFiles = require("fs")
        .readdirSync(analyticsDir)
        .filter((file: string) => file.endsWith(".json"));

      for (const file of analyticsFiles) {
        const analyticsPath = join(analyticsDir, file);
        const analyticsData = JSON.parse(readFileSync(analyticsPath, "utf-8"));
        this.analytics.set(analyticsData.prompt_id, analyticsData);
      }
    } catch (error) {
      console.error("Error loading analytics:", error);
    }
  }

  async listPrompts(args: any) {
    const { package_name, limit = 10 } = args;
    let allPrompts: Prompt[] = [];

    if (package_name) {
      const packageData = this.packages.get(package_name);
      if (packageData) {
        allPrompts = packageData.prompts;
      }
    } else {
      for (const packageData of this.packages.values()) {
        allPrompts.push(...packageData.prompts);
      }
    }

    const limitedPrompts = allPrompts.slice(0, limit);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              prompts: limitedPrompts,
              total: allPrompts.length,
              returned: limitedPrompts.length,
            },
            null,
            2
          ),
        },
      ],
    };
  }

  async getPrompt(args: any) {
    const { prompt_id, version, package_name } = args;

    let foundPrompt: Prompt | undefined;

    if (package_name) {
      const packageData = this.packages.get(package_name);
      if (packageData) {
        foundPrompt = packageData.prompts.find(
          (p) => p.id === prompt_id && (!version || p.version === version)
        );
      }
    } else {
      for (const packageData of this.packages.values()) {
        foundPrompt = packageData.prompts.find(
          (p) => p.id === prompt_id && (!version || p.version === version)
        );
        if (foundPrompt) break;
      }
    }

    if (!foundPrompt) {
      throw new Error(
        `Prompt '${prompt_id}' not found${
          version ? ` (version ${version})` : ""
        }`
      );
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(foundPrompt, null, 2),
        },
      ],
    };
  }

  async searchPrompts(args: any) {
    const { query, tags, limit = 10 } = args;
    const results: Prompt[] = [];

    for (const packageData of this.packages.values()) {
      for (const prompt of packageData.prompts) {
        const matchesQuery =
          prompt.name.toLowerCase().includes(query.toLowerCase()) ||
          prompt.content.toLowerCase().includes(query.toLowerCase()) ||
          prompt.description?.toLowerCase().includes(query.toLowerCase());

        const matchesTags =
          !tags || tags.some((tag: string) => prompt.tags.includes(tag));

        if (matchesQuery && matchesTags) {
          results.push(prompt);
        }
      }
    }

    // Sort by usage count and success rate
    results.sort((a, b) => {
      const aScore = (a.usage_count || 0) + (a.success_rate || 0) * 100;
      const bScore = (b.usage_count || 0) + (b.success_rate || 0) * 100;
      return bScore - aScore;
    });

    const limitedResults = results.slice(0, limit);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              results: limitedResults,
              total: results.length,
              returned: limitedResults.length,
            },
            null,
            2
          ),
        },
      ],
    };
  }

  async preprocessInput(args: any) {
    const { input_text, transformations, prompt_id } = args;

    let processedText = input_text;
    const appliedTransformations: string[] = [];

    // Apply transformations
    const defaultTransformations = ["intent_normalization", "noise_removal"];
    const transformsToApply = transformations || defaultTransformations;

    for (const transform of transformsToApply) {
      switch (transform) {
        case "intent_normalization":
          processedText = this.normalizeIntent(processedText);
          appliedTransformations.push("intent_normalization");
          break;
        case "noise_removal":
          processedText = this.removeNoise(processedText);
          appliedTransformations.push("noise_removal");
          break;
        case "format_standardization":
          processedText = this.standardizeFormat(processedText);
          appliedTransformations.push("format_standardization");
          break;
      }
    }

    const confidence = this.calculateConfidence(input_text, processedText);

    const result: ProcessedInput = {
      original_input: input_text,
      processed_input: processedText,
      transformations_applied: appliedTransformations,
      confidence,
    };

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private normalizeIntent(text: string): string {
    let normalized = text.toLowerCase().trim();

    // Remove common greetings
    normalized = normalized.replace(/^(hi|hello|hey)\s*,?\s*/i, "");

    // Normalize question patterns
    normalized = normalized.replace(/can you (.*)/i, "$1");
    normalized = normalized.replace(/could you (.*)/i, "$1");
    normalized = normalized.replace(/would you (.*)/i, "$1");
    normalized = normalized.replace(/please (.*)/i, "$1");
    normalized = normalized.replace(/tell me (.*)/i, "explain $1");
    normalized = normalized.replace(/how does (.*) work/i, "explain $1");
    normalized = normalized.replace(/what is (.*)/i, "define $1");

    return normalized.trim();
  }

  private removeNoise(text: string): string {
    let cleaned = text;

    // Remove filler words
    const noisePatterns = [
      /\b(um|uh|like|you know|basically|literally)\b/gi,
      /\b(please|thanks|thank you)\b/gi,
      /\b(can you|could you|would you)\b/gi,
    ];

    for (const pattern of noisePatterns) {
      cleaned = cleaned.replace(pattern, "");
    }

    // Remove extra punctuation
    cleaned = cleaned.replace(/[!]{2,}/g, "!");
    cleaned = cleaned.replace(/[?]{2,}/g, "?");
    cleaned = cleaned.replace(/[.]{2,}/g, ".");

    return cleaned.trim();
  }

  private standardizeFormat(text: string): string {
    // Remove extra whitespace
    let formatted = text.replace(/\s+/g, " ").trim();

    // Fix punctuation spacing
    formatted = formatted.replace(/\s+([,.!?])/g, "$1");
    formatted = formatted.replace(/([,.!?])([A-Za-z])/g, "$1 $2");

    // Capitalize first letter
    if (formatted && formatted[0].toLowerCase() === formatted[0]) {
      formatted = formatted[0].toUpperCase() + formatted.slice(1);
    }

    return formatted;
  }

  private calculateConfidence(original: string, processed: string): number {
    if (original === processed) {
      return 1.0;
    }

    // Simple similarity calculation
    const originalChars = new Set(original.toLowerCase());
    const processedChars = new Set(processed.toLowerCase());

    const intersection = new Set(
      [...originalChars].filter((x) => processedChars.has(x))
    );
    const union = new Set([...originalChars, ...processedChars]);

    const similarity = intersection.size / union.size;

    if (similarity > 0.8) return 0.9;
    if (similarity > 0.6) return 0.7;
    if (similarity > 0.4) return 0.5;
    return 0.3;
  }

  async gradePromptExecution(args: any) {
    const {
      prompt_id,
      user_input,
      ai_response,
      expected_outcome,
      grader_type = "rule_based",
    } = args;

    let grade: PromptGrade;

    if (grader_type === "llm" && this.openai) {
      grade = await this.gradeWithLLM(
        prompt_id,
        user_input,
        ai_response,
        expected_outcome
      );
    } else {
      grade = this.gradeWithRules(
        prompt_id,
        user_input,
        ai_response,
        expected_outcome
      );
    }

    // Update analytics
    this.updateAnalytics(grade);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(grade, null, 2),
        },
      ],
    };
  }

  private async gradeWithLLM(
    prompt_id: string,
    user_input: string,
    ai_response: string,
    expected_outcome?: string
  ): Promise<PromptGrade> {
    if (!this.openai) {
      throw new Error("OpenAI client not initialized");
    }

    const gradingPrompt = `
Rate this AI response on a scale of 1-10 for each criterion:

User asked: "${user_input}"
AI responded: "${ai_response}"
Expected outcome: "${expected_outcome || "N/A"}"

Criteria:
- Accuracy (1-10): Is the response factually correct and accurate?
- Helpfulness (1-10): Does the response help the user achieve their goal?
- Completeness (1-10): Does the response fully address the user's question?
- Clarity (1-10): Is the response clear and easy to understand?

Return JSON only:
{
  "overall_score": <number>,
  "accuracy": <number>,
  "helpfulness": <number>,
  "completeness": <number>,
  "clarity": <number>,
  "reasoning": "<explanation>"
}
`;

    try {
      const response = await this.openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: gradingPrompt }],
        temperature: 0.1,
      });

      const gradeData = JSON.parse(response.choices[0].message.content || "{}");

      return {
        prompt_id,
        user_input,
        ai_response,
        overall_score: gradeData.overall_score || 5.0,
        accuracy: gradeData.accuracy || 5.0,
        helpfulness: gradeData.helpfulness || 5.0,
        completeness: gradeData.completeness || 5.0,
        clarity: gradeData.clarity || 5.0,
        reasoning: gradeData.reasoning || "LLM grading",
        grader_type: "llm",
        is_successful: (gradeData.overall_score || 5.0) >= 7.0,
      };
    } catch (error) {
      throw new Error(`LLM grading failed: ${error}`);
    }
  }

  private gradeWithRules(
    prompt_id: string,
    user_input: string,
    ai_response: string,
    expected_outcome?: string
  ): PromptGrade {
    const accuracy = this.scoreAccuracy(user_input, ai_response);
    const helpfulness = this.scoreHelpfulness(user_input, ai_response);
    const completeness = this.scoreCompleteness(user_input, ai_response);
    const clarity = this.scoreClarity(ai_response);

    const overallScore = (accuracy + helpfulness + completeness + clarity) / 4;

    return {
      prompt_id,
      user_input,
      ai_response,
      overall_score: overallScore,
      accuracy,
      helpfulness,
      completeness,
      clarity,
      reasoning: "Rule-based grading",
      grader_type: "rule_based",
      is_successful: overallScore >= 7.0,
    };
  }

  private scoreAccuracy(user_input: string, ai_response: string): number {
    let score = 5.0;

    const errorIndicators = [
      "i don't know",
      "i can't",
      "i'm not sure",
      "i don't have access",
    ];
    if (
      errorIndicators.some((indicator) =>
        ai_response.toLowerCase().includes(indicator)
      )
    ) {
      score -= 2.0;
    }

    if (ai_response.length > 50) {
      score += 1.0;
    }

    return Math.max(1.0, Math.min(10.0, score));
  }

  private scoreHelpfulness(user_input: string, ai_response: string): number {
    let score = 5.0;

    if (ai_response.length > user_input.length * 0.5) {
      score += 2.0;
    }

    const actionWords = ["here's", "you can", "try", "use", "follow", "steps"];
    if (actionWords.some((word) => ai_response.toLowerCase().includes(word))) {
      score += 1.0;
    }

    return Math.max(1.0, Math.min(10.0, score));
  }

  private scoreCompleteness(user_input: string, ai_response: string): number {
    let score = 5.0;

    if (ai_response.length > user_input.length * 2) {
      score += 2.0;
    }

    if (
      ai_response.split("\n").length > 2 ||
      ai_response.split(".").length > 3
    ) {
      score += 1.0;
    }

    return Math.max(1.0, Math.min(10.0, score));
  }

  private scoreClarity(ai_response: string): number {
    let score = 5.0;

    if (ai_response.includes("\n")) {
      score += 1.0;
    }

    const sentences = ai_response.split(".");
    if (sentences.length > 1) {
      const avgLength =
        sentences.reduce((sum, s) => sum + s.length, 0) / sentences.length;
      if (avgLength > 10 && avgLength < 50) {
        score += 1.0;
      }
    }

    return Math.max(1.0, Math.min(10.0, score));
  }

  private updateAnalytics(grade: PromptGrade): void {
    const existing = this.analytics.get(grade.prompt_id);

    if (existing) {
      existing.total_uses += 1;
      if (grade.is_successful) {
        existing.successful_uses += 1;
      } else {
        existing.failed_uses += 1;
      }
      existing.success_rate = existing.successful_uses / existing.total_uses;

      // Update average score
      existing.average_score =
        (existing.average_score * (existing.total_uses - 1) +
          grade.overall_score) /
        existing.total_uses;
      existing.last_updated = new Date().toISOString();
    } else {
      this.analytics.set(grade.prompt_id, {
        prompt_id: grade.prompt_id,
        total_uses: 1,
        successful_uses: grade.is_successful ? 1 : 0,
        failed_uses: grade.is_successful ? 0 : 1,
        success_rate: grade.is_successful ? 1.0 : 0.0,
        average_score: grade.overall_score,
        common_failures: [],
        improvement_suggestions: [],
        last_updated: new Date().toISOString(),
      });
    }
  }

  async getPromptAnalytics(args: any) {
    const { prompt_id } = args;
    const analytics = this.analytics.get(prompt_id);

    if (!analytics) {
      throw new Error(`No analytics found for prompt '${prompt_id}'`);
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(analytics, null, 2),
        },
      ],
    };
  }

  async getBestPrompt(args: any) {
    const { user_input, context } = args;

    // Simple prompt selection based on input analysis
    const inputLower = user_input.toLowerCase();
    let bestPrompt: Prompt | undefined;

    // Find prompts that match the input intent
    for (const packageData of this.packages.values()) {
      for (const prompt of packageData.prompts) {
        const promptTags = prompt.tags.map((t) => t.toLowerCase());

        if (inputLower.includes("code") && promptTags.includes("code")) {
          bestPrompt = prompt;
          break;
        } else if (
          inputLower.includes("customer") &&
          promptTags.includes("customer")
        ) {
          bestPrompt = prompt;
          break;
        } else if (
          inputLower.includes("explain") &&
          promptTags.includes("educational")
        ) {
          bestPrompt = prompt;
          break;
        }
      }
      if (bestPrompt) break;
    }

    // Fallback to most used prompt
    if (!bestPrompt) {
      let mostUsed: Prompt | undefined;
      let maxUsage = 0;

      for (const packageData of this.packages.values()) {
        for (const prompt of packageData.prompts) {
          if (prompt.usage_count > maxUsage) {
            maxUsage = prompt.usage_count;
            mostUsed = prompt;
          }
        }
      }
      bestPrompt = mostUsed;
    }

    if (!bestPrompt) {
      throw new Error("No prompts available");
    }

    // Preprocess the input for this prompt
    const processedInput = await this.preprocessInput({
      input_text: user_input,
      prompt_id: bestPrompt.id,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              prompt: bestPrompt,
              processed_input: JSON.parse(processedInput.content[0].text),
              original_input: user_input,
            },
            null,
            2
          ),
        },
      ],
    };
  }

  async trackPromptUsage(args: any) {
    const { prompt_id, user_input, response_time, token_usage } = args;

    // Find and update the prompt usage count
    for (const packageData of this.packages.values()) {
      const prompt = packageData.prompts.find((p) => p.id === prompt_id);
      if (prompt) {
        prompt.usage_count += 1;
        break;
      }
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              message: "Usage tracked successfully",
              prompt_id,
              usage_count: "incremented",
            },
            null,
            2
          ),
        },
      ],
    };
  }
}
