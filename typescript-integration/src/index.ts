import { spawn } from "child_process";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { config } from "dotenv";

// Load environment variables from .env file
config();

export interface AIProviderConfig {
  provider?: "anthropic" | "openai" | "google";
  model?: string;
  apiKey?: string;
}

export interface CrawlerConfig {
  url: string;
  delay?: number;
  maxPages?: number;
  output?: string;
  ai?: AIProviderConfig;
}

export interface CrawlerResult {
  products: Array<{
    productName: string;
    url: string;
  }>;
  pagesProcessed: number;
  totalNodes: number;
  baseUrl: string;
  domain: string;
}

export interface CrawlerProgress {
  type: "progress" | "error" | "complete";
  message: string;
  data?: any;
}

export class AIWebCrawler {
  private pythonCommand: string;

  constructor() {
    // Detect Python command (python3 on Unix, python on Windows)
    this.pythonCommand = os.platform() === "win32" ? "python" : "python3";
  }

  /**
   * Create AI configuration for Python backend
   */
  private createAIConfig(aiConfig?: AIProviderConfig): any {
    const defaultProvider = "anthropic";
    const defaultModel = "claude-sonnet-4-20250514";

    return {
      ai_provider: aiConfig?.provider || defaultProvider,
      ai_model: aiConfig?.model || defaultModel,
    };
  }

  /**
   * Check if the Python crawler package is installed
   */
  async checkInstallation(): Promise<boolean> {
    return new Promise((resolve) => {
      const process = spawn(
        this.pythonCommand,
        ["-c", 'import src.main; print("OK")'],
        {
          stdio: "pipe",
        }
      );

      process.on("exit", (code) => {
        resolve(code === 0);
      });

      process.on("error", () => {
        resolve(false);
      });
    });
  }

  /**
   * Install the Python crawler package
   */
  async installCrawler(): Promise<void> {
    return new Promise((resolve, reject) => {
      console.log("Installing AI web crawler Python package...");

      const process = spawn("pip", ["install", "bim-category-url-crawler"], {
        stdio: "inherit",
      });

      process.on("exit", (code) => {
        if (code === 0) {
          console.log("AI web crawler installed successfully!");
          resolve();
        } else {
          reject(new Error(`Installation failed with code ${code}`));
        }
      });

      process.on("error", (error) => {
        reject(new Error(`Installation failed: ${error.message}`));
      });
    });
  }

  /**
   * Run the crawler with the given configuration
   */
  async crawl(
    config: CrawlerConfig,
    onProgress?: (progress: CrawlerProgress) => void
  ): Promise<CrawlerResult> {
    // Validate required environment variables
    if (!process.env.CLAUDE_API_KEY) {
      throw new Error(
        "CLAUDE_API_KEY environment variable is required. Please set it in your .env file."
      );
    }

    // Create temporary config file
    const tempDir = os.tmpdir();
    const configPath = path.join(tempDir, `crawler-config-${Date.now()}.json`);

    const crawlerConfig = {
      url: config.url,
      delay: config.delay || 1.5,
      max_pages: config.maxPages || 50,
      output: config.output,
      ...this.createAIConfig(config.ai),
    };

    // Write config to temp file
    fs.writeFileSync(configPath, JSON.stringify(crawlerConfig, null, 2));

    try {
      // Check installation first
      const isInstalled = await this.checkInstallation();
      if (!isInstalled) {
        if (onProgress) {
          onProgress({
            type: "progress",
            message: "Python crawler not found, attempting installation...",
          });
        }
        await this.installCrawler();
      }

      return new Promise((resolve, reject) => {
        if (onProgress) {
          onProgress({
            type: "progress",
            message: `Starting crawler for: ${config.url}`,
          });
        }

        // Spawn Python process
        const pythonProcess = spawn(
          this.pythonCommand,
          ["-m", "src.main", configPath],
          {
            stdio: ["pipe", "pipe", "pipe"],
            env: { ...process.env, CLAUDE_API_KEY: process.env.CLAUDE_API_KEY },
          }
        );

        let outputBuffer = "";
        let errorBuffer = "";

        // Handle stdout (progress and results)
        pythonProcess.stdout?.on("data", (data) => {
          const output = data.toString();
          outputBuffer += output;

          if (onProgress) {
            // Parse progress messages
            const lines = output.split("\n").filter((line) => line.trim());
            for (const line of lines) {
              if (line.includes("INFO") || line.includes("Processing")) {
                onProgress({
                  type: "progress",
                  message: line.trim(),
                });
              }
            }
          }
        });

        // Handle stderr
        pythonProcess.stderr?.on("data", (data) => {
          const error = data.toString();
          errorBuffer += error;

          if (onProgress) {
            onProgress({
              type: "error",
              message: error.trim(),
            });
          }
        });

        // Handle process completion
        pythonProcess.on("exit", (code) => {
          // Clean up temp file
          try {
            fs.unlinkSync(configPath);
          } catch (e) {
            // Ignore cleanup errors
          }

          if (code === 0) {
            try {
              // Find the output file
              let outputFile = config.output;
              if (!outputFile) {
                // Parse output to find auto-generated filename
                const match = outputBuffer.match(
                  /Results saved to: (.+\.json)/
                );
                if (match) {
                  outputFile = match[1];
                }
              }

              if (outputFile && fs.existsSync(outputFile)) {
                const results = JSON.parse(
                  fs.readFileSync(outputFile, "utf-8")
                );

                if (onProgress) {
                  onProgress({
                    type: "complete",
                    message: `Crawling completed! Found ${
                      results.products?.length || 0
                    } products.`,
                    data: results,
                  });
                }

                resolve({
                  products: results.products || [],
                  pagesProcessed: results.pages_processed || 0,
                  totalNodes: results.total_nodes || 0,
                  baseUrl: results.base_url || config.url,
                  domain: results.domain || "",
                });
              } else {
                reject(
                  new Error("Output file not found after crawling completed")
                );
              }
            } catch (error) {
              reject(new Error(`Failed to parse results: ${error}`));
            }
          } else {
            reject(
              new Error(
                `Crawler failed with code ${code}${
                  errorBuffer ? ": " + errorBuffer : ""
                }`
              )
            );
          }
        });

        pythonProcess.on("error", (error) => {
          // Clean up temp file
          try {
            fs.unlinkSync(configPath);
          } catch (e) {
            // Ignore cleanup errors
          }

          reject(new Error(`Failed to start crawler: ${error.message}`));
        });
      });
    } catch (error) {
      // Clean up temp file on error
      try {
        fs.unlinkSync(configPath);
      } catch (e) {
        // Ignore cleanup errors
      }
      throw error;
    }
  }
}

// Export default instance
export default AIWebCrawler;
