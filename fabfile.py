import fh_fablib as fl


fl.require("1.0.20241122.2")
fl.config.update(
    domain="traduire.feinheit.dev",
    branch="main",
    remote="production",
)


ns = fl.Collection(*fl.GENERAL)
