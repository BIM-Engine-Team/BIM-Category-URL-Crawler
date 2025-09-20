import { spawn } from "child_process";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { config } from "dotenv";

// Load environment variables from .env file in the TypeScript project root
config({ path: path.resolve(process.cwd(), '.env') });

export interface CrawlerResult {
  products: Array<{
    productName: string;
    url: string;
  }>;
  pages_processed: number;
  total_nodes: number;
  base_url: string;
  domain: string;
}

/**
 * Main entry function that acts as src.main for TypeScript projects.
 * Takes a config file path and outputs JSON results, exactly like the Python main.py
 *
 * @param configPath Path to the JSON configuration file
 * @returns Promise<CrawlerResult> The crawling results
 */
export async function aiCrawler(configPath: string): Promise<CrawlerResult> {
  // Validate config file exists
  if (!fs.existsSync(configPath)) {
    throw new Error(`Config file not found: ${configPath}`);
  }

  // Validate required environment variables
  if (!process.env.CLAUDE_API_KEY && !process.env.ANTHROPIC_API_KEY) {
    throw new Error(
      "CLAUDE_API_KEY or ANTHROPIC_API_KEY environment variable is required. Please set it in your .env file."
    );
  }

  // Detect Python command
  const pythonCommand = os.platform() === "win32" ? "python" : "python3";

  return new Promise((resolve, reject) => {
    // Spawn Python process with the config file, mirroring main.py behavior
    const pythonProcess = spawn(
      pythonCommand,
      ["-m", "src.main", configPath],
      {
        stdio: ["pipe", "pipe", "pipe"],
        env: {
          ...process.env,
          CLAUDE_API_KEY: process.env.CLAUDE_API_KEY || process.env.ANTHROPIC_API_KEY
        },
        cwd: path.resolve(__dirname, '../..')
      }
    );

    let outputBuffer = "";
    let errorBuffer = "";

    // Capture stdout
    pythonProcess.stdout?.on("data", (data) => {
      outputBuffer += data.toString();
    });

    // Capture stderr
    pythonProcess.stderr?.on("data", (data) => {
      errorBuffer += data.toString();
    });

    // Handle process completion
    pythonProcess.on("exit", (code) => {
      if (code === 0) {
        try {
          // Parse the config to determine output file location
          const configData = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
          let outputFile = configData.output;

          // If no output specified, look for auto-generated filename in output
          if (!outputFile) {
            const match = outputBuffer.match(/Final results: (.+\.json)/);
            if (match) {
              outputFile = match[1];
            } else {
              // Fallback: look for any JSON file mentioned in output
              const fallbackMatch = outputBuffer.match(/([^\s]+\.json)/);
              if (fallbackMatch) {
                outputFile = fallbackMatch[1];
              }
            }
          }

          if (outputFile && fs.existsSync(outputFile)) {
            const results = JSON.parse(fs.readFileSync(outputFile, "utf-8"));
            resolve({
              products: results.products || [],
              pages_processed: results.pages_processed || 0,
              total_nodes: results.total_nodes || 0,
              base_url: results.base_url || configData.url || "",
              domain: results.domain || ""
            });
          } else {
            reject(new Error("Output file not found after crawling completed. Output: " + outputBuffer));
          }
        } catch (error) {
          reject(new Error(`Failed to parse results: ${error}. Output: ${outputBuffer}`));
        }
      } else {
        reject(
          new Error(
            `Crawler failed with exit code ${code}. Error: ${errorBuffer}. Output: ${outputBuffer}`
          )
        );
      }
    });

    pythonProcess.on("error", (error) => {
      reject(new Error(`Failed to start Python crawler process: ${error.message}`));
    });
  });
}

// Export as default for easy importing
export default aiCrawler;