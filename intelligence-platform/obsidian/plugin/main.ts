import {
  App,
  Notice,
  Plugin,
  PluginSettingTab,
  Setting,
  TFile,
  requestUrl,
} from "obsidian";

interface IPSettings {
  apiBaseUrl: string;
  autoSendOnCreate: boolean;
}

const DEFAULTS: IPSettings = {
  apiBaseUrl: "https://api.example.com",
  autoSendOnCreate: true,
};

export default class IntelligencePlugin extends Plugin {
  settings!: IPSettings;

  async onload() {
    await this.loadSettings();

    this.addCommand({
      id: "send-current-to-platform",
      name: "Send current note to Intelligence Platform",
      callback: () => this.sendActive(),
    });

    this.addCommand({
      id: "open-generated-report",
      name: "Open generated report for current note",
      callback: () => this.openReport(),
    });

    if (this.settings.autoSendOnCreate) {
      this.registerEvent(
        this.app.vault.on("create", async (file) => {
          if (file instanceof TFile && file.path.startsWith("raw/news/")) {
            await this.send(file);
          }
        }),
      );
    }

    this.addSettingTab(new IPSettingsTab(this.app, this));
  }

  async sendActive() {
    const f = this.app.workspace.getActiveFile();
    if (!f) return new Notice("No active file");
    await this.send(f);
  }

  async send(file: TFile) {
    try {
      const content = await this.app.vault.read(file);
      const hash = await sha256(content);
      const resp = await requestUrl({
        url: `${this.settings.apiBaseUrl}/v1/ingest`,
        method: "POST",
        contentType: "application/json",
        body: JSON.stringify({
          vault_path: file.path,
          content_hash: `sha256:${hash}`,
          title: file.basename,
          raw_text: content,
          language: "vi",
        }),
      });
      new Notice(`Sent: ${resp.json?.status ?? "ok"}`);
    } catch (e: any) {
      new Notice(`Send failed: ${e.message}`);
    }
  }

  async openReport() {
    const f = this.app.workspace.getActiveFile();
    if (!f) return;
    const date = new Date().toISOString().slice(0, 10);
    const path = `Processed/master/${date}.md`;
    const existing = this.app.vault.getAbstractFileByPath(path);
    if (existing instanceof TFile) {
      await this.app.workspace.getLeaf(false).openFile(existing);
    } else {
      new Notice(`No report yet at ${path}`);
    }
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULTS, await this.loadData());
  }
  async saveSettings() {
    await this.saveData(this.settings);
  }
}

class IPSettingsTab extends PluginSettingTab {
  plugin: IntelligencePlugin;
  constructor(app: App, plugin: IntelligencePlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display() {
    const { containerEl } = this;
    containerEl.empty();
    new Setting(containerEl)
      .setName("API base URL")
      .setDesc("Where your FastAPI lives. e.g. https://api.example.com")
      .addText((t) =>
        t.setValue(this.plugin.settings.apiBaseUrl).onChange(async (v) => {
          this.plugin.settings.apiBaseUrl = v;
          await this.plugin.saveSettings();
        }),
      );
    new Setting(containerEl)
      .setName("Auto-send on create")
      .setDesc("Automatically POST new files in raw/news to the API")
      .addToggle((t) =>
        t.setValue(this.plugin.settings.autoSendOnCreate).onChange(async (v) => {
          this.plugin.settings.autoSendOnCreate = v;
          await this.plugin.saveSettings();
        }),
      );
  }
}

async function sha256(s: string): Promise<string> {
  const enc = new TextEncoder().encode(s);
  const buf = await crypto.subtle.digest("SHA-256", enc);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
