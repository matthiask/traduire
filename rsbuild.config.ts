import fs from "node:fs"
import { defineConfig } from "@rsbuild/core"

/* Django and fablib integration starts here */
const development = process.env.NODE_ENV === "development"
const template = "./tmp/template.html"

fs.existsSync("./tmp") || fs.mkdirSync("./tmp")
fs.writeFileSync(template, "<head><title></title></head>")
!development &&
  fs.existsSync("./static") &&
  fs.rmSync("./static", { recursive: true })

const integration = {
  output: {
    dataUriLimit: 500,
    cleanDistPath: false,
    distPath: {
      root: development ? "./tmp/dev" : ".",
      html: "static",
    },
  },
  dev: {
    assetPrefix: true,
    writeToDisk: (path) => /\.html$/.test(path),
  },
  html: {
    template,
    meta: false,
  },
  server: { printUrls: false },
}
/* Django and fablib integration ends here */

export default defineConfig({
  ...integration,
  source: {
    entry: {
      main: "./frontend/main.js",
    },
  },
  tools: {
    postcss(config, { addPlugins }) {
      addPlugins([require("postcss-nesting")(), require("autoprefixer")()])
    },
  },
})
