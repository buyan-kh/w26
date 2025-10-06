export declare class PromptRegistryMCP {
    private registryPath;
    private packages;
    private analytics;
    private openai?;
    constructor();
    private loadPackages;
    private loadAnalytics;
    listPrompts(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    getPrompt(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    searchPrompts(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    preprocessInput(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    private normalizeIntent;
    private removeNoise;
    private standardizeFormat;
    private calculateConfidence;
    gradePromptExecution(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    private gradeWithLLM;
    private gradeWithRules;
    private scoreAccuracy;
    private scoreHelpfulness;
    private scoreCompleteness;
    private scoreClarity;
    private updateAnalytics;
    getPromptAnalytics(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    getBestPrompt(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    trackPromptUsage(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
}
//# sourceMappingURL=prompt-registry-mcp.d.ts.map