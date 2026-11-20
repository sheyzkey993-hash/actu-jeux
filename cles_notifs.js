// Fabrique la paire de clés des notifications. À lancer une seule fois : node cles_notifs.js
// - la clé publique est écrite dans site/index.html
// - la clé privée est écrite dans cle_privee_notifs.txt (jamais envoyé sur GitHub : à coller dans les secrets)
const { generateKeyPairSync } = require("crypto");
const fs = require("fs");
const path = require("path");

const prive = path.join(__dirname, "cle_privee_notifs.txt");
const page = path.join(__dirname, "site", "index.html");
if (fs.existsSync(prive)) {
  console.log("Les clés existent déjà, rien n'est changé.");
  process.exit(0);
}
const jwk = generateKeyPairSync("ec", { namedCurve: "prime256v1" }).privateKey.export({ format: "jwk" });
const publique = Buffer.concat([Buffer.from([4]), Buffer.from(jwk.x, "base64url"), Buffer.from(jwk.y, "base64url")]).toString("base64url");
const html = fs.readFileSync(page, "utf8");
if (!html.includes('CLE_PUBLIQUE = "A_REMPLIR"')) throw new Error("Emplacement de la clé publique introuvable dans index.html");
fs.writeFileSync(prive, jwk.d);
fs.writeFileSync(page, html.replace('CLE_PUBLIQUE = "A_REMPLIR"', `CLE_PUBLIQUE = "${publique}"`));
console.log("Clé publique écrite dans la page, clé privée dans cle_privee_notifs.txt");
