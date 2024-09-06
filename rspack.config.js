module.exports = (env, argv) => {
  const { base, devServer, assetRule, postcssRule, swcWithPreactRule } =
    require("./rspack.library.js")(argv.mode === "production")

  return {
    ...base,
    devServer: devServer({ backendPort: env.backend }),
    module: {
      rules: [
        assetRule(),
        postcssRule({
          plugins: ["postcss-nesting", "autoprefixer"],
        }),
        swcWithPreactRule(),
      ],
    },
  }
}
