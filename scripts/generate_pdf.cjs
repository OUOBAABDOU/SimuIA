const PDFDocument = require('pdfkit');
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, '..', 'public');
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
}

const pdfPath = path.join(publicDir, 'Lean_Canvas_SimuEmploi_AI.pdf');

// Create document with Landscape A4 dimensions (841.89 x 595.28 points)
const doc = new PDFDocument({
  size: 'A4',
  layout: 'landscape',
  margin: 20
});

const writeStream = fs.createWriteStream(pdfPath);
doc.pipe(writeStream);

// Colors
const PRIMARY = '#312e81'; // Indigo 900
const ACCENT = '#4f46e5';  // Indigo 600
const SECONDARY = '#0f172a'; // Slate 900
const BORDER_COLOR = '#94a3b8'; // Slate 400
const BG_HEADER = '#f1f5f9';
const TEXT_MUTED = '#475569';

// Header section
doc.rect(20, 15, 801.89, 45).fill('#1e1b4b');

doc.fillColor('#ffffff')
   .fontSize(18)
   .font('Helvetica-Bold')
   .text('LEAN CANVAS : SimuEmploi AI', 30, 22, { width: 780, align: 'left' });

doc.fontSize(9)
   .font('Helvetica')
   .fillColor('#c7d2fe')
   .text('Plateforme de Simulation d\'Entretien & Coaching Comportemental IA  |  Date: ' + new Date().toLocaleDateString('fr-FR'), 30, 43);

// Layout grid definition
// Width: 801.89 pt total. 5 columns of ~158 pt width each.
const marginX = 20;
const startY = 65;
const colWidth = (801.89 - 4 * 6) / 5; // ~155.5 pt
const topRowHeight = 350; // top 5 columns
const bottomRowHeight = 150; // bottom 2 columns

function drawBlock(x, y, w, h, title, question, items, extraSubSection = null) {
  // Background box
  doc.rect(x, y, w, h).fillAndStroke('#ffffff', BORDER_COLOR);

  // Title Header bar
  doc.rect(x, y, w, 22).fill('#e0e7ff');
  doc.fillColor(PRIMARY)
     .font('Helvetica-Bold')
     .fontSize(8.5)
     .text(title.toUpperCase(), x + 5, y + 6, { width: w - 10, lineBreak: false });

  let currentY = y + 26;

  if (question) {
    doc.fillColor(TEXT_MUTED)
       .font('Helvetica-Oblique')
       .fontSize(7)
       .text('"' + question + '"', x + 5, currentY, { width: w - 10 });
    currentY += doc.heightOfString('"' + question + '"', { width: w - 10, fontSize: 7 }) + 4;
  }

  // Items
  doc.fillColor(SECONDARY).font('Helvetica').fontSize(7);
  if (Array.isArray(items)) {
    items.forEach(item => {
      const text = '• ' + item;
      const textHeight = doc.heightOfString(text, { width: w - 10, fontSize: 7 });
      if (currentY + textHeight <= y + h - 5) {
        doc.text(text, x + 5, currentY, { width: w - 10 });
        currentY += textHeight + 2;
      }
    });
  } else if (typeof items === 'string') {
    doc.text(items, x + 5, currentY, { width: w - 10 });
    currentY += doc.heightOfString(items, { width: w - 10, fontSize: 7 }) + 4;
  }

  // Extra subsection (like Alternatives or Early Adopters)
  if (extraSubSection && currentY < y + h - 30) {
    currentY += 2;
    doc.moveTo(x + 5, currentY).lineTo(x + w - 5, currentY).strokeColor('#cbd5e1').stroke();
    currentY += 4;

    doc.fillColor('#0369a1').font('Helvetica-Bold').fontSize(8)
       .text(extraSubSection.title, x + 5, currentY, { width: w - 10 });
    currentY += 10;

    if (extraSubSection.question) {
      doc.fillColor(TEXT_MUTED).font('Helvetica-Oblique').fontSize(6.5)
         .text('"' + extraSubSection.question + '"', x + 5, currentY, { width: w - 10 });
      currentY += doc.heightOfString('"' + extraSubSection.question + '"', { width: w - 10, fontSize: 6.5 }) + 3;
    }

    doc.fillColor(SECONDARY).font('Helvetica').fontSize(6.5);
    extraSubSection.items.forEach(item => {
      const text = '- ' + item;
      const textHeight = doc.heightOfString(text, { width: w - 10, fontSize: 6.5 });
      if (currentY + textHeight <= y + h - 4) {
        doc.text(text, x + 5, currentY, { width: w - 10 });
        currentY += textHeight + 2;
      }
    });
  }
}

// 1. Problem (Col 0)
const x0 = marginX;
drawBlock(x0, startY, colWidth, topRowHeight,
  "1. Problème",
  "Quels sont les problèmes de ce qui existe déjà ?",
  [
    "Stress élevé et manque de préparation réaliste des candidats avant un entretien.",
    "Absence de retours objectifs et immédiats sur le non-verbal (posture, regard) et la voix (tics, hésitations).",
    "Coût prohibitif (80-200€/h) et indisponibilité des coachs humains.",
    "Difficulté à appliquer la méthode STAR (Situation, Tâche, Action, Résultat) spontanément."
  ],
  {
    title: "Alternatives Existantes",
    question: "Quels sont les alternatives existantes ?",
    items: [
      "Entraînement seul au miroir ou vidéo (aucun feedback).",
      "Prompts ChatGPT texte (pas d'interaction vocale/visuelle).",
      "Coaching privé humain (très cher).",
      "Vidéos conseils passives YouTube/TikTok."
    ]
  }
);

// 2. Solution & 3. Key Metrics (Col 1 stacked)
const x1 = marginX + colWidth + 6;
const halfH = (topRowHeight - 6) / 2;
drawBlock(x1, startY, colWidth, halfH,
  "2. Solution",
  "Comment délivrer cette valeur ?",
  [
    "Simulateur vidéo/vocal immersif avec avatar recruteur IA interactif (Gemini 3.6 Flash).",
    "Analyse multimodale temps réel (posture, regard, voix, tics de langage).",
    "Débriefing instantané complet avec notes STAR, transcriptions et recommandations.",
    "Bibliothèque de scénarios réels par métier et guide STAR."
  ]
);

drawBlock(x1, startY + halfH + 6, colWidth, halfH,
  "3. Indicateurs Clés",
  "Quels chiffres pour mesurer la performance ?",
  [
    "Taux de succès aux entretiens réels déclarés (NPS & success rate).",
    "Nombre de simulations complétées par utilisateur.",
    "Progression moyenne du score d'assurance (+25% après 3 sessions).",
    "MRR, Coût d'Acquisition (CAC) et LTV."
  ]
);

// 4. Unique Value Proposition (Col 2)
const x2 = marginX + (colWidth + 6) * 2;
drawBlock(x2, startY, colWidth, topRowHeight,
  "4. Proposition de Valeur",
  "Quel est votre proposition de valeur ?",
  "Le seul coach d'entretien intelligent accessible 24/7 qui combine un recruteur virtuel adaptatif en temps réel et une analyse simultanée du fond (méthode STAR) et de la forme (voix, posture et regard).",
  {
    title: "Offre Simplifiée",
    question: "Formulation condensée",
    items: [
      "\"Permettre aux étudiants et chercheurs d'emploi de surmonter le stress des entretiens pour décrocher leur poste idéal grâce à des simulations immersives guidées par l'IA.\""
    ]
  }
);

// 5. Unfair Advantage & 6. Channels (Col 3 stacked)
const x3 = marginX + (colWidth + 6) * 3;
drawBlock(x3, startY, colWidth, halfH,
  "5. Avantage Compétitif",
  "Difficile à copier ?",
  [
    "Analyse multimodale temps réel combinée (vidéo webcam + audio + recruteur IA).",
    "Algorithme propriétaire de scoring pédagogique (évaluation STAR + posture).",
    "Boucle d'apprentissage basée sur l'analyse anonymisée d'entretiens."
  ]
);

drawBlock(x3, startY + halfH + 6, colWidth, halfH,
  "6. Canaux",
  "Comment atteindre votre cible ?",
  [
    "Partenariats B2B2C avec universités et grandes écoles.",
    "SEO ciblé sur la préparation aux entretiens et fiches métiers.",
    "Campagnes ciblées LinkedIn / TikTok / Instagram.",
    "Programme de parrainage (1 simulation gratuite par ami)."
  ]
);

// 7. Customer Segments (Col 4)
const x4 = marginX + (colWidth + 6) * 4;
drawBlock(x4, startY, colWidth, topRowHeight,
  "7. Segments Clientèles",
  "Quel est votre cible ?",
  [
    "Étudiants et jeunes diplômés préparant leurs premiers entretiens ou stages.",
    "Cadres et professionnels en reconversion ou recherche d'emploi.",
    "Écoles supérieures, universités et centres de formation (B2B/B2B2C).",
    "Cabinets de recrutement et organismes de réinsertion."
  ],
  {
    title: "Utilisateurs Pionniers",
    question: "Cible prioritaire en premier ?",
    items: [
      "Étudiants en fin d'études et jeunes diplômés ayant un entretien prévu dans les 7 à 14 jours."
    ]
  }
);

// Bottom row: 8. Cost Structure (Left 50%) & 9. Revenue Streams (Right 50%)
const bottomY = startY + topRowHeight + 8;
const bottomW = (801.89 - 6) / 2;

drawBlock(marginX, bottomY, bottomW, bottomRowHeight,
  "8. Structure de Coûts",
  "Quels sont les coûts de mise en place et fonctionnement ?",
  [
    "API Intelligence Artificielle (Gemini API raisonnement, Text-to-Speech & Speech-to-Text).",
    "Hébergement Cloud, serveurs WebRTC à faible latence et base de données sécurisée.",
    "Développement software, maintenance continue et mises à jour des modèles IA.",
    "Coûts d'acquisition marketing (Publicités ciblées, partenariats académiques)."
  ]
);

drawBlock(marginX + bottomW + 6, bottomY, bottomW, bottomRowHeight,
  "9. Sources de Revenus",
  "Quel est votre tarification ?",
  [
    "Freemium : 1 simulation découverte gratuite (5 min) avec rapport synthétique.",
    "Pass Entretien (Achat ponctuel) : 9,99€ pour un accès illimité pendant 7 jours (idéal avant un entretien).",
    "Abonnement Mensuel B2C : 19,99€ / mois sans engagement pour un coaching continu.",
    "Licences B2B Écoles & Entreprises : Tarification annuelle sur mesure au volume d'utilisateurs."
  ]
);

// Footer
doc.fillColor('#94a3b8').fontSize(7).font('Helvetica-Oblique')
   .text('Document généré pour SimuEmploi AI — Lean Canvas de Modèle Économique', marginX, 580, { width: 801.89, align: 'center' });

doc.end();

writeStream.on('finish', () => {
  console.log('PDF successfully generated at:', pdfPath);
});
