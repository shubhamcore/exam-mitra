/* =========================================================
   Exam Mitra — frontend logic v2.1
   SSE, rendering, KaTeX math, expandable days, exam presets.
   Vanilla JS, no frameworks.
   ========================================================= */
const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const form             = $("#plan-form");
const submitBtn        = $("#submit-btn");
const progressSection  = $("#progress-section");
const resultsSection   = $("#results");
const stepsList        = $("#steps-list");
const toastEl          = $("#toast");

const STEP_LABELS = [
  "Queued",
  "Parsing syllabus into chapters",
  "Building your day-by-day study plan",
  "Finding best free video lectures from top Indian educators",
  "Writing revision notes with beautifully-formatted formulas",
  "Creating active-recall flashcards",
  "Generating exam-style MCQs with detailed explanations",
  "🎉 Your study package is ready!",
];
const TOTAL_STEPS = 7;

/* =========================================================
   EXAM PRESETS DATABASE — covers 60+ Indian exams
   ========================================================= */
const EXAM_PRESETS = {
  engineering: [
    { emoji: "⚡", label: "JEE Mains Full Physics", exam: "JEE Mains Physics", hours: 5,
      syllabus: "Kinematics (1D + 2D), Laws of Motion, Work Energy Power, Rotational Motion, Gravitation, Properties of Solids and Liquids, Thermodynamics, Kinetic Theory of Gases, Oscillations and Waves, Electrostatics, Current Electricity, Magnetism, EMI and AC, Electromagnetic Waves, Ray Optics, Wave Optics, Modern Physics (Dual Nature, Atoms, Nuclei), Semiconductors, Communication Systems" },
    { emoji: "🧪", label: "JEE Mains Full Chemistry", exam: "JEE Mains Chemistry", hours: 5,
      syllabus: "Some Basic Concepts of Chemistry (Mole Concept), Atomic Structure, Chemical Bonding and Molecular Structure, States of Matter, Thermodynamics and Thermochemistry, Equilibrium (Chemical + Ionic), Redox Reactions, Solutions, Electrochemistry, Chemical Kinetics, Surface Chemistry, Coordination Compounds, General Organic Chemistry (GOC), Hydrocarbons, Haloalkanes and Haloarenes, Alcohols/Phenols/Ethers, Aldehydes/Ketones/Carboxylic Acids, Amines, Biomolecules, Polymers, Chemistry in Everyday Life" },
    { emoji: "📐", label: "JEE Mains Full Maths", exam: "JEE Mains Mathematics", hours: 5,
      syllabus: "Sets, Relations and Functions, Complex Numbers and Quadratic Equations, Matrices and Determinants, Permutations and Combinations, Binomial Theorem, Sequences and Series, Trigonometry, Straight Lines, Conic Sections, Circles, Limits Continuity and Differentiability, Differentiation and Applications, Indefinite Integration, Definite Integrals and Area, Differential Equations, Vectors, Three Dimensional Geometry, Probability, Statistics, Mathematical Reasoning" },
    { emoji: "🎯", label: "Just Kinematics (quick)", exam: "JEE Mains Physics", hours: 4,
      syllabus: "Kinematics" },
    { emoji: "🔧", label: "JEE Advanced Mechanics", exam: "JEE Advanced Physics (Mechanics)", hours: 6,
      syllabus: "Kinematics in 1D and 2D (Projectile, Relative Velocity), Newton's Laws of Motion with Pulleys and Wedges, Friction, Work Power Energy, Conservation of Momentum and Collisions, Rotational Motion (Moment of Inertia, Torque, Angular Momentum, Rolling Motion), Gravitation, Fluid Mechanics, SHM, Damped and Forced Oscillations, Mechanical Waves" },
  ],
  medical: [
    { emoji: "🧬", label: "NEET Full Biology", exam: "NEET UG Biology", hours: 5,
      syllabus: "The Living World, Biological Classification, Plant Kingdom, Animal Kingdom, Morphology of Flowering Plants, Anatomy of Flowering Plants, Structural Organisation in Animals, Cell: Unit of Life, Biomolecules, Cell Cycle and Cell Division, Transport in Plants, Mineral Nutrition, Photosynthesis, Respiration in Plants, Plant Growth and Development, Digestion and Absorption, Breathing and Exchange of Gases, Body Fluids and Circulation, Excretory Products, Locomotion and Movement, Neural Control and Coordination, Chemical Coordination, Reproduction in Organisms, Human Reproduction, Reproductive Health, Principles of Inheritance (Genetics), Molecular Basis of Inheritance, Evolution, Human Health and Disease, Strategies for Food Production, Microbes in Human Welfare, Biotechnology Principles and Applications, Ecology and Environment, Biodiversity and Conservation" },
    { emoji: "⚛️", label: "NEET Physics", exam: "NEET Physics", hours: 4,
      syllabus: "Kinematics, Laws of Motion, Work Energy Power, Rotational Motion, Gravitation, Properties of Solids and Liquids, Thermodynamics, Kinetic Theory of Gases, Oscillations and Waves, Electrostatics, Current Electricity, Magnetism, EMI and AC, Ray Optics, Wave Optics, Dual Nature of Matter, Atoms and Nuclei, Semiconductor Electronics" },
    { emoji: "⚗️", label: "NEET Chemistry", exam: "NEET Chemistry", hours: 4,
      syllabus: "Mole Concept, Atomic Structure, Chemical Bonding, States of Matter, Thermodynamics, Equilibrium, Redox Reactions, Solutions, Electrochemistry, Chemical Kinetics, Coordination Compounds, General Organic Chemistry, Hydrocarbons, Haloalkanes, Alcohols/Phenols/Ethers, Aldehydes/Ketones/Carboxylic Acids, Amines, Biomolecules, Polymers, Chemistry in Everyday Life" },
    { emoji: "🩺", label: "Human Physiology (high weightage)", exam: "NEET Biology - Human Physiology", hours: 4,
      syllabus: "Digestion and Absorption, Breathing and Exchange of Gases, Body Fluids and Circulation (Blood, Heart, Cardiac Cycle, ECG), Excretory Products and Their Elimination (Kidney, Nephron, Urine Formation), Locomotion and Movement (Muscles, Bones, Joints), Neural Control and Coordination (Neuron, Brain, Reflex Action, Sense Organs), Chemical Coordination and Integration (Endocrine Glands and Hormones)" },
    { emoji: "🧪", label: "Just Cell Biology", exam: "NEET Biology", hours: 3,
      syllabus: "Cell Biology" },
  ],
  civil: [
    { emoji: "🏛️", label: "UPSC Prelims GS Complete", exam: "UPSC CSE Prelims GS Paper 1", hours: 6,
      syllabus: "Indian Polity and Constitution (Preamble, Fundamental Rights, DPSP, Parliament, Judiciary, Federalism, Local Government, Constitutional Bodies), Indian Economy (Planning, Five Year Plans, NITI Aayog, Budget, Fiscal Policy, RBI Monetary Policy, Banking, Agriculture, Industry, Infrastructure, Poverty, Unemployment), Modern Indian History (1857 Revolt, Governor Generals, Social Reform Movements, Formation of INC, Moderates vs Extremists, Gandhian Era, Independence 1947), Ancient Indian History (Indus Valley, Vedic, Maurya, Gupta, Post-Gupta), Medieval Indian History (Delhi Sultanate, Mughal Empire, Vijayanagara, Marathas), Indian Geography (Physical Features, Rivers, Climate, Soils, Vegetation, Agriculture, Minerals, Industries, Transport), World Geography (Continents, Oceans, Mountains, Rivers, Climate Zones), Environment and Ecology (Ecosystems, Biodiversity, Climate Change, Environmental Conventions, Protected Areas), General Science (Physics, Chemistry, Biology basics for Prelims), Current Affairs (last 18 months national and international)" },
    { emoji: "📋", label: "UPSC CSAT Paper 2", exam: "UPSC CSAT Paper 2", hours: 4,
      syllabus: "Reading Comprehension, Quantitative Aptitude (Number System, Percentages, Ratio Proportion, Time Speed Distance, Profit Loss, Average, Simple Interest Compound Interest), Logical Reasoning (Syllogism, Venn Diagrams, Blood Relations, Direction, Seating Arrangement, Coding-Decoding), Data Interpretation (Tables, Bar Charts, Pie Charts, Line Graphs), Basic Numeracy, Decision Making, Problem Solving, Analytical Ability, Interpersonal Skills including Communication Skills" },
    { emoji: "⚖️", label: "Indian Polity (M. Laxmikanth)", exam: "UPSC Indian Polity", hours: 5,
      syllabus: "Constitutional Framework (Making of Constitution, Preamble, Features, Schedules), Fundamental Rights, Directive Principles of State Policy, Fundamental Duties, Union Executive (President, Vice President, PM, Council of Ministers, Attorney General), Parliament (Lok Sabha, Rajya Sabha, Speaker, Committees, Bills and Law Making), Union Judiciary (Supreme Court, PIL, Judicial Review, Judicial Activism), State Government (Governor, CM, State Legislature, High Courts), Local Government (Panchayati Raj, Municipalities), Union Territories and Special Areas, Constitutional Bodies (EC, CAG, UPSC, SPSC, Finance Commission, NITI Aayog), Non-Constitutional Bodies (NDC, NHRC, CVC, CIC), Centre-State Relations, Emergency Provisions, Constitutional Amendments" },
    { emoji: "💰", label: "Indian Economy", exam: "UPSC Indian Economy", hours: 5,
      syllabus: "National Income Accounting, Economic Planning in India (Five Year Plans, NITI Aayog), Agriculture (Green Revolution, Cropping Patterns, Land Reforms, MSP, PDS, Food Security), Industry (Industrial Policy, MSME, PSUs, Make in India), Services Sector, Banking in India (RBI, Commercial Banks, NBFCs, Monetary Policy), Financial Markets (SEBI, Stock Exchanges), Public Finance (Budget, Taxation GST, Fiscal Policy, FRBM), Infrastructure (Energy, Transport, Telecom, Power), Poverty and Unemployment, Social Sector (Health, Education, MGNREGA), External Sector (BoP, FDI, FPI, Exchange Rate, WTO, IMF World Bank), Economic Survey and Union Budget Highlights" },
    { emoji: "📜", label: "Modern Indian History (Spectrum)", exam: "UPSC Modern Indian History", hours: 4,
      syllabus: "Advent of Europeans, British Conquest of India (Bengal, Mysore, Maratha, Punjab), Governor Generals (Clive to Mountbatten), 1857 Revolt, Social and Religious Reform Movements (Brahmo Samaj, Arya Samaj, Prarthana Samaj, Theosophical Society, Aligarh Movement), Formation of Indian National Congress, Moderate Phase (1885-1905), Extremist Phase and Swadeshi Movement (1905-1917), Revolutionary Terrorism, Gandhian Era (Champaran, Kheda, Ahmedabad, Non-Cooperation, Civil Disobedience, Quit India), Peasant and Tribal Movements, Left Movement, INA and Subhash Chandra Bose, Partition and Independence (1947)" },
  ],
  govt: [
    { emoji: "📝", label: "SSC CGL Tier 1", exam: "SSC CGL Tier 1", hours: 5,
      syllabus: "General Intelligence and Reasoning (Series, Coding-Decoding, Analogy, Odd One Out, Direction, Blood Relation, Venn Diagram, Mathematical Operation, Syllogism, Paper Folding, Mirror Image, Embedded Figure, Dice), Quantitative Aptitude (Number System, LCM HCF, Simplification, Percentage, Ratio Proportion, Average, Profit Loss, SI CI, Time Work, Time Speed Distance, Boat Stream, Pipe Cistern, Geometry, Mensuration, Trigonometry, Algebra, DI), English Language (Grammar, Vocabulary, Reading Comprehension, One Word Substitution, Idioms, Synonyms Antonyms, Sentence Improvement, Error Detection), General Awareness (Indian History, Polity, Geography, Economics, Physics Chemistry Biology up to 10th, Current Affairs, Static GK)" },
    { emoji: "🏦", label: "Banking IBPS/SBI PO", exam: "IBPS PO / SBI PO", hours: 5,
      syllabus: "Quantitative Aptitude (Simplification, Number Series, Quadratic Equations, Data Interpretation, Average, Percentage, Ratio Proportion, Profit Loss, SI CI, Time Work, Speed Distance, Mensuration, Probability, Permutation Combination), Reasoning Ability (Puzzle, Seating Arrangement, Syllogism, Inequality, Coding-Decoding, Blood Relation, Direction, Input Output, Alphanumeric Series, Data Sufficiency), English Language (Reading Comprehension, Grammar, Cloze Test, Para Jumbles, Error Detection, Fill in the Blanks, Vocabulary), General/Financial Awareness (Banking Terms, RBI, Monetary Policy, Budget, Economy Current Affairs, Financial Institutions), Computer Awareness (Basics, MS Office, Internet, Networking)" },
    { emoji: "🚂", label: "Railway RRB NTPC", exam: "RRB NTPC (Non-Technical Popular Categories)", hours: 4,
      syllabus: "Mathematics (Number System, Decimals Fractions, LCM HCF, Percentage, Ratio Proportion, Profit Loss, SI CI, Time Work, Time Distance, Average, Mensuration, DI), General Intelligence and Reasoning (Analogies, Series, Coding-Decoding, Puzzle, Venn Diagram, Data Sufficiency, Direction, Blood Relations), General Awareness (Indian History and Culture, Geography of India and World, Indian Polity and Constitution, Indian Economy, General Science and Technology, Current Affairs, Sports, Books and Authors, Important Days), General Science (Physics, Chemistry, Biology up to 10th standard)" },
    { emoji: "🔤", label: "SSC CHSL", exam: "SSC CHSL (10+2)", hours: 4,
      syllabus: "English Language (Spot the Error, Fill in the Blanks, Synonyms/Antonyms, Spellings, Idioms, One Word Substitution, Sentence Improvement, Active/Passive, Direct/Indirect), General Intelligence (Symbolic/Number Analogy, Series, Coding-Decoding, Venn Diagrams, Direction, Blood Relations), Quantitative Aptitude (Arithmetic, Algebra, Geometry, Mensuration, Trigonometry, DI), General Awareness (History, Polity, Geography, Science, Current Affairs)" },
  ],
  defence: [
    { emoji: "🛡️", label: "NDA Complete", exam: "NDA (National Defence Academy)", hours: 6,
      syllabus: "Mathematics (Algebra: Sets, Relations, Complex Numbers, Quadratic, Permutation Combination, Binomial, Logarithm, AP GP HP, Matrices Determinants; Trigonometry: Identities, Heights Distances; Coordinate Geometry: Straight Lines, Conic Sections; Calculus: Limits, Continuity, Differentiation, Integration, Differential Equations; Vectors, 3D, Statistics Probability), General Ability Test (English: Grammar, Comprehension, Vocabulary; GK: Physics, Chemistry, General Science, Social Studies, Indian History, Geography, Current Affairs; Physics: Motion, Force, Energy, Light, Sound, Electricity; Chemistry: Elements, Compounds, Reactions; Biology: Cells, Plants, Animals, Human Body; History: Modern India, Freedom Struggle; Geography: India and World; Polity: Constitution, Panchayati Raj)" },
    { emoji: "✈️", label: "CDS / AFCAT", exam: "CDS / AFCAT", hours: 5,
      syllabus: "English (Comprehension, Grammar, Vocabulary, Antonyms Synonyms, Error Spotting, Sentence Arrangement), General Knowledge (Indian History, Polity, Geography, Economy, General Science, Current Affairs, Defence), Elementary Mathematics (Arithmetic: Number System, HCF LCM, Percentage, Profit Loss, SI CI, Ratio, Time Work, Time Distance; Algebra: Basic Operations, Linear Equations, Quadratic, Logarithm; Trigonometry: Identities, Heights Distances; Geometry: Lines, Angles, Triangles, Circles, Mensuration; Statistics: Tabulation, Bar Charts, Pie Charts)" },
  ],
  teaching: [
    { emoji: "👩‍🏫", label: "CTET Paper 1 (Class 1-5)", exam: "CTET Paper 1 (Primary)", hours: 4,
      syllabus: "Child Development and Pedagogy (Child Development: Growth and Development, Theories (Piaget, Kohlberg, Vygotsky), Learning Theories, Inclusive Education, Assessment), Language 1 (Hindi/English: Pedagogy, Grammar, Reading Comprehension), Language 2 (English/Hindi: Comprehension, Pedagogy), Mathematics (Number System, Addition Subtraction, Multiplication Division, Fractions, Measurement, Shapes, Geometry, Data Handling, Pedagogy of Maths), Environmental Studies (EVS: Family, Friends, Food, Shelter, Water, Travel, Things We Make and Do, Pedagogy of EVS)" },
    { emoji: "👨‍🏫", label: "CTET Paper 2 (Class 6-8)", exam: "CTET Paper 2 (Upper Primary)", hours: 4,
      syllabus: "Child Development and Pedagogy (Adolescence, Learning Theories, Intelligence, Personality, Assessment and Evaluation, Inclusive Education), Language 1 (Hindi/English Pedagogy, Grammar, Comprehension), Language 2 (English/Hindi Comprehension, Pedagogy), Mathematics and Science (Number System, Algebra, Geometry, Mensuration, Data Handling; Science: Food, Materials, World of Living, How Things Work, Moving Things, Natural Phenomena, Natural Resources) OR Social Studies/Social Science (History, Geography, Social and Political Life, Pedagogy)" },
  ],
  boards: [
    { emoji: "🏫", label: "CBSE Class 10 — All Subjects", exam: "CBSE Class 10 Board Exams", hours: 4,
      syllabus: "Mathematics (Real Numbers, Polynomials, Pair of Linear Equations in Two Variables, Quadratic Equations, Arithmetic Progressions, Triangles, Coordinate Geometry, Introduction to Trigonometry, Some Applications of Trigonometry, Circles, Constructions, Areas Related to Circles, Surface Areas & Volumes, Statistics, Probability), Science (Chemical Reactions & Equations, Acids Bases & Salts, Metals & Non-metals, Carbon & its Compounds, Periodic Classification, Life Processes, Control & Coordination, How do Organisms Reproduce, Heredity & Evolution, Light Reflection & Refraction, Human Eye & Colourful World, Electricity, Magnetic Effects of Electric Current, Our Environment), Social Science (History: Nationalism in Europe, Nationalism in India, The Making of a Global World, Age of Industrialisation, Print Culture; Geography: Resources & Development, Forest & Wildlife, Water Resources, Agriculture, Minerals & Energy Resources, Manufacturing Industries, Lifelines of National Economy; Political Science: Power Sharing, Federalism, Gender Religion & Caste, Political Parties, Outcomes of Democracy, Challenges to Democracy; Economics: Development, Sectors of Indian Economy, Money & Credit, Globalisation, Consumer Rights), English (First Flight + Footprints Without Feet: comprehension, grammar tenses/modals/voice/reported speech/clauses, writing: letter/article/story), Hindi Course A/B (Kshitij, Kritika, Sparsh, Sanchayan: prose, poetry, grammar, writing)" },
    { emoji: "📐", label: "CBSE Class 10 Maths + Science", exam: "CBSE Class 10 Maths and Science", hours: 4,
      syllabus: "Mathematics (Real Numbers, Polynomials, Pair of Linear Equations, Quadratic Equations, AP, Triangles, Coordinate Geometry, Trigonometry & Applications, Circles, Constructions, Areas, Surface Areas & Volumes, Statistics, Probability), Science (Chemical Reactions, Acids Bases Salts, Metals Non-metals, Carbon Compounds, Periodic Classification, Life Processes, Control & Coordination, Reproduction, Heredity Evolution, Light Reflection & Refraction, Human Eye, Electricity, Magnetic Effects, Our Environment)" },
    { emoji: "🔬", label: "CBSE Class 12 Physics", exam: "CBSE Class 12 Physics Board Exam", hours: 4,
      syllabus: "Electrostatics (Coulomb's Law, Electric Field, Electric Dipole, Gauss's Law & Applications, Electric Potential, Capacitors, Dielectrics), Current Electricity (Ohm's Law, Kirchhoff's Laws, Wheatstone Bridge, Meter Bridge, Potentiometer, Cells in Series/Parallel), Magnetic Effects of Current (Biot-Savart, Ampere's Law, Solenoid, Force on Moving Charge, Cyclotron, Torque on Current Loop, Moving Coil Galvanometer), Magnetism & Matter (Bar Magnet, Magnetism & Gauss's Law, Earth's Magnetism, Magnetic Properties), EMI & AC (Faraday's Law, Lenz Law, Eddy Currents, Self/Mutual Inductance, AC Generator, Transformer, LCR Circuits, Power Factor, Resonance, Wattless Current), Electromagnetic Waves (EM Spectrum, Displacement Current), Ray Optics (Reflection, Refraction, TIR, Lens, Mirror, Prism, Microscope, Telescope, Refraction through Spherical Surfaces), Wave Optics (Huygens Principle, Interference, YDSE, Diffraction, Single Slit, Polarisation, Brewster's Law, Resolving Power), Dual Nature of Radiation & Matter (Photoelectric Effect, Einstein's Equation, de Broglie Relation, Davisson-Germer), Atoms (Rutherford, Bohr Model, Hydrogen Spectrum), Nuclei (Mass Defect, Binding Energy, Radioactivity Alpha/Beta/Gamma Decay, Nuclear Fission, Nuclear Fusion, Half Life, Mean Life), Semiconductor Electronics (Intrinsic/Extrinsic Semiconductors, P-N Junction Diode, Zener Diode, LED, Photodiode, Solar Cell, Transistor as Amplifier/Switch, Logic Gates: OR AND NOT NAND NOR), Communication Systems (Propagation, Amplitude Modulation, Basic Communication Blocks)" },
    { emoji: "🧪", label: "CBSE Class 12 Chemistry", exam: "CBSE Class 12 Chemistry Board Exam", hours: 4,
      syllabus: "Solutions (Types, Expressing Concentration, Solubility, Vapour Pressure, Raoult's Law, Ideal/Non-ideal Solutions, Colligative Properties, Van't Hoff Factor), Electrochemistry (Galvanic Cell, EMF, Nernst Equation, Gibbs Energy, Conductance, Kohlrausch's Law, Electrolysis, Batteries, Fuel Cells, Corrosion), Chemical Kinetics (Rate of Reaction, Factors, Rate Law, Order & Molecularity, Integrated Rate Equations Zero/First Order, Half Life, Pseudo First Order, Arrhenius Equation, Activation Energy, Collision Theory), d & f Block Elements (Electronic Configurations, Oxidation States, Interstitial Compounds, Alloys, Lanthanoids Actinoids, Mischmetall), Coordination Compounds (Werner's Theory, VBT, CFT, IUPAC Nomenclature, Isomerism, CFT Splitting, Colour, Magnetic Properties, Bonding, Applications in Extraction/Analysis/Medicines), Haloalkanes & Haloarenes (Nomenclature, SN1 SN2 Mechanisms, Chirality, Optical Rotation, Grignard Reagent), Alcohols Phenols Ethers (Nomenclature, Preparation, Properties, Lucas Test, Williamson Synthesis), Aldehydes Ketones Carboxylic Acids (Nomenclature, Preparation, Reactions, Nucleophilic Addition, Cannizzaro, Aldol Condensation, HVZ, Esterification), Amines (Nomenclature, Basic Strength, Preparation, Reactions, Diazonium Salts), Biomolecules (Carbohydrates: Mono/Disaccharides, Polysaccharides, Reducing/Non-reducing Sugars; Proteins: Amino Acids, Peptide Bonds, Primary/Secondary/tertiary Structure, Enzymes; Nucleic Acids: DNA/RNA; Vitamins Classification), Polymers (Classification, Addition/Condensation, Copolymer, Important Polymers: Polythene, Nylon, PVC, Teflon, Bakelite, Buna-N/S, Rubber), Chemistry in Everyday Life (Drugs: Analgesics, Antibiotics, Antiseptics, Antacids, Antihistamines; Chemicals in Food: Preservatives, Artificial Sweeteners; Cleansing Agents: Soaps Detergents)" },
    { emoji: "🧬", label: "CBSE Class 12 Biology", exam: "CBSE Class 12 Biology Board Exam", hours: 4,
      syllabus: "Reproduction in Organisms (Asexual, Sexual), Sexual Reproduction in Flowering Plants (Stamen, Pistil, Pollination, Double Fertilisation, Endosperm Embryo Development, Seed, Apomixis), Human Reproduction (Male/Female Reproductive System, Spermatogenesis, Oogenesis, Menstrual Cycle, Fertilisation, Implantation, Pregnancy, Parturition, Lactation), Reproductive Health (Population, Birth Control, MTP, STIs, Infertility, ART IVF ZIFT GIFT), Principles of Inheritance & Variation (Mendel's Laws, Incomplete Dominance, Codominance, Multiple Alleles, Dihybrid Cross, Chromosomal Theory, Linkage Recombination, Sex Determination, Pedigree, Mendelian Disorders, Chromosomal Disorders Down Klinefelter Turner), Molecular Basis of Inheritance (DNA as Genetic Material, Griffith/Avery/Hershey-Chase, DNA Replication, Transcription, Translation Genetic Code, Lac Operon, Human Genome Project, DNA Fingerprinting), Evolution (Origin of Life, Darwinism, Lamarckism, Hardy-Weinberg, Adaptive Radiation, Human Evolution), Human Health & Disease (Pathogens, Immunity Innate/Acquired, Vaccines, Allergies, Autoimmunity, AIDS Cancer, Drugs Alcohol), Strategies for Enhancement in Food Production (Animal Husbandry, Plant Breeding, Tissue Culture, Single Cell Protein), Microbes in Human Welfare (Household Products, Industrial, Sewage Treatment, Biogas, Biocontrol, Biofertilisers), Biotechnology (Principles: Restriction Enzymes, PCR, Cloning Vectors; Applications: Bt Cotton, Pest Resistant Plants, Insulin, Gene Therapy, Transgenic Animals, Ethical Issues), Organisms & Populations (Organism & Environment, Population Attributes Growth Models, Population Interactions Predation Mutualism Parasitism), Ecosystem (Structure, Productivity, Decomposition, Energy Flow 10% Law, Ecological Pyramids, Succession, Carbon Phosphorus Cycle), Biodiversity & Conservation (Levels, Patterns, Importance, Loss, In-situ/Ex-situ Conservation, Endangered Species, Hotspots, Red Data Book, National Parks Sanctuaries), Environmental Issues (Air/Water/Noise Pollution, Solid Wastes, Greenhouse Effect, Global Warming, Ozone Depletion, Deforestation, Eutrophication, Biomagnification)" },
    { emoji: "📊", label: "CBSE Class 12 Maths", exam: "CBSE Class 12 Mathematics Board Exam", hours: 5,
      syllabus: "Relations & Functions (Types of Relations: Reflexive Symmetric Transitive Equivalence, One-One Onto Inverse Functions, Composite Functions, Binary Operations), Inverse Trigonometric Functions (Principal Value Branch, Properties), Matrices (Order, Types, Addition Multiplication, Transpose, Symmetric Skew, Invertible Matrices, Elementary Operations), Determinants (Properties, Area of Triangle, Minors Cofactors, Adjoint, Inverse, System of Linear Equations, Cramer's Rule), Continuity & Differentiability (Continuity of Functions, Differentiability, Derivatives of Composite/Implicit/Inverse Trigonometric/Exponential/Logarithmic Functions, Logarithmic Differentiation, Parametric Forms, Second Order Derivatives, Rolle's & Lagrange's MVT), Applications of Derivatives (Rate of Change, Increasing/Decreasing, Tangents Normals, Approximations, Maxima Minima, Word Problems), Integrals (Indefinite: Substitution, Partial Fractions, By Parts, Standard Forms; Definite Integral Properties, Fundamental Theorem, Limit of Sum, Area between two curves), Applications of Integrals (Area under simple curves: lines circles parabolas ellipses; area between two curves), Differential Equations (Order Degree, General/Particular Solutions, Variable Separable, Homogeneous DE, Linear DE of form dy/dx + Py = Q), Vectors (Scalar/Vector, Magnitude, Direction Cosines, Addition, Dot Product, Cross Product, Projection, Scalar Triple Product), 3D Geometry (Direction Ratios Cosines, Line in Space Cartesian & Vector Equation, Angle between Two Lines, Shortest Distance, Plane in Normal/Intercept Form, Distance from Point to Plane, Angle between Planes, Co-planarity), Linear Programming (Formulation of LPP, Graphical Solution, Feasible Region, Corner Point Method, Bounded/Unbounded), Probability (Conditional Probability, Multiplication Theorem, Independent Events, Total Probability, Bayes' Theorem, Random Variables Probability Distribution, Mean Variance, Bernoulli Trials, Binomial Distribution)" },
    { emoji: "📖", label: "CBSE Class 12 English Core", exam: "CBSE Class 12 English Core Board Exam", hours: 2,
      syllabus: "Reading (Unseen Passages: Factual/Descriptive/Literary, Note-Making), Writing Skills (Notice, Advertisement, Poster, Formal/Informal Invitation & Reply, Letter to Editor, Application for Job, Article, Report, Speech, Debate), Grammar (Tenses, Clauses, Determiners, Active/Passive, Reported Speech, Prepositions, Modals), Literature (Flamingo Prose: Last Lesson, Lost Spring, Deep Water, The Rattrap, Indigo, Going Places, Poets & Pancakes, The Interview; Flamingo Poetry: My Mother at Sixty-six, Keeping Quiet, A Thing of Beauty, A Roadside Stand, Aunt Jennifer's Tigers; Vistas: Third Level, Tiger King, The Enemy, On the Face of It, Should Wizard hit Mommy, Evans tries an O-level, Memories of Childhood)" },
    { emoji: "🏴", label: "Bihar Board (BSEB) Class 10/12", exam: "Bihar Board (BSEB) Class 10 or 12", hours: 4,
      syllabus: "Bihar School Examination Board (BSEB / Bihar Board) Class 10 or Class 12. BSEB follows NCERT pattern with Bihar-specific questions. Choose subject(s): Mathematics, Science (Physics Chemistry Biology), Social Science (History: India & Contemporary World Bihar's role (Champaran Satyagraha, JP Movement, Bihar in Freedom Struggle), Geography (Resources, Agriculture, Bihar rivers Kosi/Gandak/Sone/Ganga, Industries in Bihar), Political Science/Civics (Federalism, Bihar Panchayati Raj), Economics (Development, Sectors of Bihar Economy)), Hindi, English, Sanskrit. Exam pattern: 50% objective (1-mark MCQs), 30% short answer (2/3 marks), 20% long answer (5 marks); total 100 marks (Theory 80 + Practical/Internal 20 in applicable subjects). Include Bihar GK: Chhath Puja, Madhubani painting, Bodhgaya, Nalanda, Rajgir, Vaishali, Jayaprakash Narayan, Dr Rajendra Prasad, Karpoori Thakur, Dashrath Manjhi." },
    { emoji: "🌾", label: "UP Board Class 10/12", exam: "UP Board (UPMSP) Class 10 or 12", hours: 4,
      syllabus: "Uttar Pradesh Madhyamik Shiksha Parishad Class 10 or 12. UP Board follows NCERT pattern in Hindi and English medium. Choose subject: गणित (Maths), विज्ञान (Science), सामाजिक विज्ञान (Social Science: History with UP Freedom Movement 1857 Chauri-Chaura, Geography of UP: Ganga Yamuna Doab, Agriculture, Mughal Awadh, Chikankari Kathak; Civics, Economics), हिन्दी, English, Sanskrit. UP Board paper pattern: 70 marks theory + 30 marks internal/practical, mix of very short (1 mark), short (2-3 marks), long (5-8 marks) answers; objective MCQ section of 20 marks." },
    { emoji: "🏛", label: "ICSE Class 10 / ISC Class 12", exam: "ICSE Class 10 or ISC Class 12 (CISCE)", hours: 4,
      syllabus: "Indian Certificate of Secondary Education (ICSE, Class 10) or Indian School Certificate (ISC, Class 12) by CISCE. ICSE compulsory: English Language & Literature, Second Language (Hindi/Sanskrit/Regional), History-Civics-Geography, Mathematics, Science (Physics/Chemistry/Biology); electives: Computer Applications, Economics, Commercial Studies, Physical Education, Art, Environmental Science etc. ISC three/four electives: Physics, Chemistry, Maths/Biology, Computer Science, Commerce, Accounts, Business Studies, Economics, History, Geography, Political Science, Sociology, Psychology, English. ICSE/ISC has 20% internal assessment/project work in every subject; exam pattern includes MCQs, short answers, long essays, practicals." },
    { emoji: "🌴", label: "Maharashtra / Other State Board", exam: "Other State Board (Class 10/12)", hours: 4,
      syllabus: "Type your state board, class, and subjects. Works for: Maharashtra HSC/SSC, Rajasthan RBSE/BSER, Madhya Pradesh MPBSE, West Bengal WBCHSE/WBBSE, Tamil Nadu Samacheer Kalvi, Karnataka SSLC/2nd PUC, Kerala SSLC/HSE, Andhra Pradesh BIEAP, Telangana TSBIE, Gujarat GSEB, Punjab PSEB, Haryana HBSE, Odisha CHSE/BSE, Jharkhand JAC, Chhattisgarh CGBSE, Assam SEBA/AHSEC, J&K JKBOSE. Tell me the subject(s) and I will build a complete NCERT-based board plan with PYQ focus." },
  ],
  state: [
    { emoji: "🗺️", label: "BPSC Prelims (Bihar)", exam: "BPSC Prelims (Bihar PSC)", hours: 5, lang: "hinglish",
      syllabus: "General Studies: General Science (Physics, Chemistry, Biology basics), History of India and Bihar (Ancient: Bihar in Mahajanapadas, Maurya Empire, Ashoka; Medieval: Bihar under Delhi Sultanate and Mughals; Modern: Bihar in Freedom Struggle, Champaran, Gandhiji in Bihar), Geography of India and Bihar (Physical Features, Rivers of Bihar (Kosi, Gandak, Sone, Ganga), Agriculture, Minerals, Industries, Transport), Indian Polity and Economy (Constitution, Panchayati Raj, Bihar Panchayati Raj Act, Five Year Plans, Bihar Economy: Agriculture, Industries, Infrastructure, Growth), National Movement and Role of Bihar, General Mental Ability, Current Events of National and International Importance, Bihar Special: Culture, Festivals (Chhath), Fairs, Folk Dances, Tourism, Personalities of Bihar (Jayaprakash Narayan, Rajendra Prasad, Kunwar Singh, Karpoori Thakur)" },
    { emoji: "🕌", label: "UPPSC Prelims (Uttar Pradesh)", exam: "UPPSC Prelims (UP PCS)", hours: 5,
      syllabus: "General Studies Paper 1: History of India (Ancient, Medieval, Modern with focus on UP: Rama, Krishna, Buddha, Mahavira, Mughal Awadh, 1857 in UP, UP in Freedom Struggle), Geography of India and UP (Physical, Rivers of UP: Ganga, Yamuna, Gomti, Ghaghara; Agriculture, Minerals, Industries in UP), Indian Polity and Governance (Constitution, UP Panchayati Raj, State Administration), Indian Economy and UP Economy (Agriculture in UP, MSME, One District One Product, Infrastructure), General Science, Current Affairs, UP Special (Culture: Kathak, Ramlila, Chikankari, Festivals, Personalities, Demography, Education)", lang: "en" },
    { emoji: "🐅", label: "MPSC (Maharashtra)", exam: "MPSC Rajyaseva Prelims", hours: 5,
      syllabus: "General Studies: History of India and Maharashtra (Maratha Empire (Shivaji, Peshwas), Bhakti Movement in Maharashtra, Maharashtra in Freedom Struggle, Samyukta Maharashtra Movement, Reformers: Jyotiba Phule, Ambedkar, Savitribai Phule), Geography of India and Maharashtra (Physical: Western Ghats, Konkan, Deccan Plateau; Rivers of Maharashtra: Godavari, Krishna, Bhima; Agriculture, Industries, Mumbai), Indian Polity and Constitution, Economy (Indian and Maharashtra Economy: Agriculture, Sugar Industry, IT in Pune/Mumbai, MIDC), General Science, Environment, Current Affairs, Maharashtra Special: Culture (Lavani, Tamasha, Warli, Ganesh Chaturthi), Tourism (Ajanta, Ellora), Personalities" },
    { emoji: "🏰", label: "RPSC RAS (Rajasthan)", exam: "RPSC RAS Prelims (Rajasthan PSC)", hours: 5,
      syllabus: "General Studies: History, Art Culture Literature Tradition of Rajasthan (Ancient Kingdoms: Mewar, Marwar; Forts: Chittorgarh, Mehrangarh; Folk Dances: Ghoomar, Kalbeliya; Fairs: Pushkar; Festivals: Teej, Gangaur; Literature: Meera, Surdas), Geography of Rajasthan (Thar Desert, Aravalli Range, Rivers: Chambal, Luni; Wildlife: Ranthambore, Keoladeo; Minerals: Copper, Zinc, Salt), Indian History, Geography of India, Indian Polity Constitution, Indian Economy, Science and Technology, Reasoning and Mental Ability, Current Affairs National and Rajasthan" },
    { emoji: "🦁", label: "GPSC (Gujarat)", exam: "GPSC Gujarat PSC Prelims", hours: 5,
      syllabus: "General Studies: History of India and Gujarat (Ancient: Indus Valley (Dholavira, Lothal), Solanki Dynasty; Medieval: Gujarat Sultanate; Modern: Freedom Movement in Gujarat, Gandhi in Gujarat, Dandi March, Bardoli Satyagraha), Geography of India and Gujarat (Physical Features, Rivers of Gujarat: Narmada, Tapi, Sabarmati; Rann of Kutch, Gir Forest; Industries: Textiles, Petrochemicals, Diamond Polishing), Indian Polity and Constitution, Economy of India and Gujarat, General Science, Current Affairs" },
  ],
  other: [
    { emoji: "🎓", label: "CUET UG", exam: "CUET UG (Central Universities Entrance Test)", hours: 4,
      syllabus: "Language Section (English/Hindi: Comprehension, Grammar, Vocabulary, Verbal Ability), Domain Subjects (choose: Physics, Chemistry, Maths, Biology, History, Geography, Polity, Economics, Accountancy, Business Studies, Psychology, Sociology, etc. — NCERT Class 12 level), General Test (General Knowledge and Current Affairs, General Mental Ability, Numerical Ability, Quantitative Reasoning, Logical and Analytical Reasoning)" },
    { emoji: "⚙️", label: "GATE Engineering", exam: "GATE (Engineering Graduate Aptitude)", hours: 6,
      syllabus: "Engineering Mathematics (Linear Algebra, Calculus, Differential Equations, Complex Variables, Probability Statistics, Numerical Methods), Core Engineering Subject topics (varies by branch: Computer Science, Mechanical, Electrical, Civil, Electronics etc. — include full branch-specific syllabus from GATE syllabus), General Aptitude (Verbal Ability: Grammar, Sentence Completion, Analogies; Numerical Ability: Numerical Computation, Estimation, Data Interpretation)" },
    { emoji: "📊", label: "CAT MBA Entrance", exam: "CAT (Common Admission Test for IIMs)", hours: 5,
      syllabus: "Verbal Ability and Reading Comprehension (Reading Passages, Para Jumbles, Odd One Out, Para Summary, Sentence Correction, Vocabulary), Data Interpretation and Logical Reasoning (Tables, Bar Charts, Pie Charts, Line Graphs, Seating Arrangements, Puzzles, Blood Relations, Syllogisms, Grid-Based DI, Caselets), Quantitative Aptitude (Arithmetic: Percentages, Profit Loss, Ratio, Time Work, Time Speed, SI/CI; Algebra: Linear Equations, Quadratics, Functions, Progressions; Geometry and Mensuration; Number System; Modern Maths: Permutation Combination, Probability, Set Theory, Logarithms)" },
  ],
  college: [
    { emoji: "🎓", label: "B.Tech 1st Year Engineering Physics", exam: "B.Tech First Year Engineering Physics", hours: 5,
      syllabus: "Quantum Mechanics (Wave-Particle Duality, de Broglie, Uncertainty Principle, Schrödinger Equation), Electromagnetic Theory (Maxwell's Equations, EM Waves), Optics (Interference, Diffraction, Polarization, Lasers, Fiber Optics), Solid State Physics (Crystal Structure, X-ray Diffraction, Band Theory), Special Theory of Relativity, Nuclear Physics (Radioactivity, Fission, Fusion), Semiconductor Physics (Diodes, Transistors, ICs)" },
    { emoji: "⚡", label: "B.Tech 1st Year Engineering Maths", exam: "B.Tech First Year Engineering Mathematics", hours: 5,
      syllabus: "Differential Calculus (Limits, Continuity, Differentiability, Partial Differentiation, Maxima Minima), Integral Calculus (Definite Indefinite, Multiple Integrals, Beta Gamma Functions), Linear Algebra (Matrices, Determinants, Eigenvalues Eigenvectors, Vector Spaces), Differential Equations (ODE first/higher order, PDE basics), Vector Calculus (Gradient Divergence Curl, Green Gauss Stokes Theorems), Complex Analysis (Analytic Functions, Cauchy-Riemann, Integration, Residues), Probability and Statistics (Random Variables, Distributions, Regression)" },
    { emoji: "💻", label: "B.Tech CSE Data Structures & Algorithms", exam: "B.Tech CSE - Data Structures and Algorithms", hours: 6,
      syllabus: "Arrays and Strings, Linked Lists (Singly, Doubly, Circular), Stacks and Queues (with applications), Trees (Binary Trees, BST, AVL, Red-Black, B-Tree), Heaps and Priority Queues, Graphs (Representation, BFS, DFS, Shortest Paths Dijkstra/Bellman-Ford, MST Kruskal/Prim), Sorting (Bubble, Insertion, Selection, Merge, Quick, Heap, Counting, Radix), Searching (Linear, Binary, Interpolation, Hashing), Dynamic Programming (Knapsack, LCS, Matrix Chain), Algorithm Analysis (Time Complexity, Big O, Recurrence Relations)" },
    { emoji: "🔌", label: "B.Tech Basic Electrical Engineering", exam: "B.Tech First Year Basic Electrical Engineering", hours: 4,
      syllabus: "DC Circuits (Ohm's Law, KVL KCL, Network Theorems: Thevenin, Norton, Superposition, Maximum Power Transfer), AC Circuits (Single Phase, Three Phase, Phasors, Power Factor), Transformers, DC Machines (Generators Motors), AC Machines (Induction Motor, Synchronous Motor), Measuring Instruments, Basics of Power Systems" },
    { emoji: "🧪", label: "BSc Physics (General)", exam: "BSc Physics (Graduation)", hours: 5,
      syllabus: "Classical Mechanics (Newtonian, Lagrangian, Hamiltonian), Thermodynamics and Statistical Physics, Electromagnetism, Optics (Geometrical Physical), Quantum Mechanics, Atomic and Molecular Physics, Solid State Physics, Nuclear and Particle Physics, Electronics (Analog Digital)" },
    { emoji: "📊", label: "BCom / BBA Subjects", exam: "BCom/BBA University Exams", hours: 4,
      syllabus: "Financial Accounting (Journal, Ledger, Trial Balance, Final Accounts, Partnership), Business Economics (Demand Supply, Market Structures, National Income), Business Mathematics (Calculus, Matrices, Linear Programming, Financial Maths), Business Law (Indian Contract Act, Companies Act), Marketing Management, HR Management, Financial Management (Capital Budgeting, WACC, Working Capital)" },
    { emoji: "💊", label: "MBBS First Year (Pre-clinical)", exam: "MBBS First Year (Anatomy, Physiology, Biochemistry)", hours: 6,
      syllabus: "Gross Anatomy (Upper Limb, Lower Limb, Thorax, Abdomen, Head Neck, Neuroanatomy, Histology, Embryology), Physiology (General, Nerve Muscle, Blood, Nerve, Cardiovascular, Respiratory, Renal, GI, Endocrine, Reproductive, CNS), Biochemistry (Biomolecules: Carbohydrates, Proteins, Lipids, Enzymes, Metabolism, Vitamins, Minerals, Molecular Biology)" },
    { emoji: "⚖️", label: "BA LLB / Law Semester", exam: "BA LLB / LLB Law University Exams", hours: 5,
      syllabus: "Constitutional Law of India (Fundamental Rights, DPSP, Union State Executive, Judiciary), Indian Penal Code (IPC), Law of Torts, Contract Act, Criminal Procedure Code (CrPC), Civil Procedure Code (CPC), Family Law, Administrative Law, Jurisprudence (Schools of Jurisprudence, Rights Duties, Legal Concepts)" },
    { emoji: "🖥️", label: "BTech CSE Operating Systems", exam: "BTech CSE - Operating Systems", hours: 5,
      syllabus: "OS Structures, Processes and Threads, CPU Scheduling (FCFS, SJF, Round Robin, Priority), Process Synchronization (Semaphores, Monitors, Classical Problems), Deadlocks (Detection, Prevention, Avoidance, Banker's Algorithm), Memory Management (Paging, Segmentation, Virtual Memory, Page Replacement), File Systems (Allocation Methods, Free Space, Directory), I/O Systems, Security Protection" },
    { emoji: "🗄️", label: "BTech CSE DBMS", exam: "BTech CSE - Database Management Systems", hours: 5,
      syllabus: "DBMS Architecture (3-Schema), ER Model (Entities, Attributes, Relationships, Cardinality), Relational Model (Keys, Constraints, Relational Algebra), SQL (DDL, DML, Joins, Views, Subqueries), Normalization (1NF to BCNF, Functional Dependencies), Transactions (ACID, Concurrency Control, Locking, Timestamp), Indexing and Hashing, Recovery (Log-based, Checkpoints), NoSQL basics" },
    { emoji: "🌐", label: "BTech CSE Computer Networks", exam: "BTech CSE - Computer Networks", hours: 5,
      syllabus: "Network Models (OSI 7-layer, TCP/IP), Physical Layer (Signals, Bandwidth, Transmission Media), Data Link Layer (Framing, Error Detection CRC, MAC Protocols: ALOHA, CSMA/CD/CA, Ethernet), Network Layer (IP Addressing IPv4/IPv6, Subnetting, Routing: OSPF, BGP, RIP, ICMP, ARP), Transport Layer (TCP UDP, 3-way Handshake, Flow Control, Congestion Control), Application Layer (HTTP, FTP, DNS, SMTP, DHCP), Network Security (Cryptography, SSL/TLS, Firewalls)" },
    { emoji: "🔢", label: "BTech ECE/EE Digital Electronics", exam: "BTech ECE/EE - Digital Electronics / Logic Design", hours: 4,
      syllabus: "Number Systems (Binary, Octal, Hex, Signed/Unsigned, Codes BCD Gray), Boolean Algebra (Theorems, Simplification K-Maps up to 5 var, Quine-McCluskey), Logic Gates (AND OR NOT NAND NOR XOR XNOR, Universal Gates), Combinational Circuits (Adders, Subtractors, MUX, DEMUX, Encoder, Decoder, ALU), Sequential Circuits (Latches, Flip-Flops SR JK D T, Counters: Sync Async, Registers, Shift Registers), Memory (RAM ROM PLA PAL), ADC/DAC, Finite State Machines (Moore, Mealy)" },
    { emoji: "⚙️", label: "BTech ME Thermodynamics", exam: "BTech Mechanical - Engineering Thermodynamics", hours: 5,
      syllabus: "Basic Concepts (System, Surroundings, Properties, Processes, Zeroth Law), First Law of Thermodynamics (Energy Conservation, Internal Energy, Enthalpy, Steady Flow Energy Equation), Second Law (Kelvin-Planck, Clausius, Carnot Cycle, Entropy, Availability), Pure Substances (Steam Tables, Mollier Chart, Rankine Cycle), Gas Power Cycles (Otto, Diesel, Dual, Brayton), Refrigeration Cycles (VCRS, Reverse Carnot, COP), Psychrometrics, IC Engines" },
    { emoji: "📚", label: "Custom / Any syllabus", exam: "Self Study (College/University)", hours: 4,
      syllabus: "Type your specific subject, semester subjects, or topics from your college syllabus. Works for BTech, BSc, BCom, BA, BCA, BBA, MBA, MCA, MBBS, BDS, Law, Pharmacy, Nursing, Hotel Mgmt, etc." },
  ],
};

/* Exam preset UI */
const catRow = $("#cat-row");
const examRow = $("#exam-row");
const examLabel = $("#exam-label");

function renderExamChips(category) {
  examRow.innerHTML = "";
  const list = EXAM_PRESETS[category] || [];
  list.forEach((p, idx) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "preset-chip exam-chip" + (idx === 0 ? " active" : "");
    b.dataset.exam = p.exam;
    b.dataset.hours = p.hours;
    b.dataset.syllabus = p.syllabus;
    if (p.lang) b.dataset.lang = p.lang;
    b.innerHTML = `<span class="emoji">${p.emoji}</span> ${p.label}`;
    b.addEventListener("click", () => applyPreset(p, b));
    examRow.appendChild(b);
  });
  // Auto-apply first exam chip in the selected category
  if (list.length > 0) {
    $("#exam").value = list[0].exam;
    $("#hours").value = list[0].hours;
    $("#syllabus").value = list[0].syllabus;
    if (list[0].lang) $("#language").value = list[0].lang;
  }
}

function applyPreset(p, chip) {
  $("#exam").value = p.exam;
  $("#hours").value = p.hours;
  $("#syllabus").value = p.syllabus;
  if (p.lang) $("#language").value = p.lang;
  $$(".exam-chip").forEach(c => c.classList.remove("active"));
  if (chip) chip.classList.add("active");
  toast("✅ Preset loaded — review and click Generate!");
}

$$(".cat-chip").forEach(cat => {
  cat.addEventListener("click", () => {
    $$(".cat-chip").forEach(c => c.classList.remove("active"));
    cat.classList.add("active");
    renderExamChips(cat.dataset.cat);
  });
});

// Initialize with engineering category visible
renderExamChips("engineering");



/* ---- utilities ---- */
function esc(s) {
  return (s == null ? "" : String(s)).replace(
    /[&<>"']/g,
    c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
  );
}

function toast(msg, ms = 2200) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toastEl.classList.remove("show"), ms);
}

/* ---- KaTeX math rendering ---- */
function renderMathIn(root) {
  const render = () => {
    if (!window.renderMathInElement) {
      // KaTeX not loaded yet — retry shortly
      setTimeout(() => renderMathIn(root), 150);
      return;
    }
    try {
      renderMathInElement(root, {
        delimiters: [
          {left: "$$", right: "$$", display: true},
          {left: "$",  right: "$",  display: false},
          {left: "\\(", right: "\\)", display: false},
          {left: "\\[", right: "\\]", display: true},
        ],
        throwOnError: false,
        errorColor: "#dc2626",
        strict: "ignore",
      });
    } catch (e) {
      console.warn("KaTeX render error:", e);
    }
  };
  if (document.readyState === "complete" || window.__katexReady) {
    render();
  } else {
    window.addEventListener("load", render, {once: true});
  }
}
window.__renderKatex = () => renderMathIn(document);

/* ---- find resources for a given day/chapter keyword ---- */
function resourcesForDay(chapterTitle, allResources) {
  if (!allResources || !chapterTitle) return [];
  const kw = chapterTitle.toLowerCase();
  const scored = allResources.map(r => {
    const rt = (r.chapter || "").toLowerCase();
    const title = (r.title || "").toLowerCase();
    let score = 0;
    // exact chapter match
    if (rt === kw) score += 100;
    else if (rt && kw.includes(rt.slice(0, Math.min(rt.length, 10)))) score += 30;
    // word overlap with chapter title
    const words = kw.split(/\s+/).filter(w => w.length > 3);
    for (const w of words) {
      if (rt.includes(w)) score += 5;
      if (title.includes(w)) score += 2;
    }
    return {r, score};
  });
  scored.sort((a, b) => b.score - a.score);
  return scored.filter(s => s.score >= 5).slice(0, 3).map(s => s.r);
}

/* ---- progress rendering ---- */
function renderProgress(currentStep, counts = {}) {
  progressSection.classList.remove("hidden");
  stepsList.innerHTML = "";
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    let label = STEP_LABELS[i] || `Step ${i}`;
    if (i === 1 && counts.chapters) label += ` — ${counts.chapters} chapters identified`;
    if (i === 2 && counts.days)     label += ` — ${counts.days} days planned`;
    if (i === 3 && counts.resources)label += ` — ${counts.resources} resources curated`;
    if (i === 4 && counts.notes)    label += ` — ${counts.notes} notes, ${counts.flashcards||0} cards, ${counts.mcqs||0} MCQs`;
    const isDone   = i < currentStep;
    const isActive = i === currentStep;
    const div = document.createElement("div");
    div.className = "step" + (isDone ? " done" : isActive ? " active" : "");
    div.innerHTML = `
      <div class="step-icon"><span class="step-num">${i}</span></div>
      <div class="step-label">${label}${isActive ? "…" : ""}</div>
      <div class="step-count">${isDone ? "✓" : ""}</div>`;
    stepsList.appendChild(div);
  }
}

function resetForm() {
  submitBtn.disabled = false;
  submitBtn.classList.remove("loading");
  submitBtn.querySelector(".btn-text").textContent = "✨ Generate my study plan";
}

/* ---- SSE ---- */
function connectSSE(jobId) {
  return new Promise((resolve) => {
    const es = new EventSource(`/api/jobs/${jobId}/stream`);
    let finished = false;

    es.onmessage = e => {
      try {
        const data = JSON.parse(e.data);
        const ev = data.event;
        if (ev === "init" || ev === "progress") {
          renderProgress(data.step || 1, data);
        } else if (ev === "step_complete") {
          renderProgress(data.step + 1, data);
        } else if (ev === "complete") {
          renderProgress(TOTAL_STEPS, data);
          finished = true;
          es.close();
          setTimeout(() => loadAndRenderResults(jobId), 600);
          resolve();
        } else if (ev === "error") {
          finished = true;
          es.close();
          showError(data.message || "Something went wrong. Please try again.");
          resetForm();
          resolve();
        } else if (ev === "close") {
          es.close();
          if (!finished) resolve();
        }
      } catch (err) { console.error("SSE parse error:", err); }
    };
    es.onerror = () => {
      console.warn("SSE connection hiccup, will retry…");
    };
  });
}

/* ---- form submit ---- */
form.addEventListener("submit", async e => {
  e.preventDefault();
  submitBtn.disabled = true;
  submitBtn.classList.add("loading");
  submitBtn.querySelector(".btn-text").textContent = "Starting agents";

  resultsSection.classList.add("hidden");
  resultsSection.innerHTML = "";
  progressSection.classList.remove("hidden");
  renderProgress(1);
  progressSection.scrollIntoView({ behavior: "smooth", block: "start" });

  const payload = {
    exam:         $("#exam").value.trim(),
    syllabus:     $("#syllabus").value.trim(),
    daily_hours:  parseFloat($("#hours").value) || 4,
    start_date:   $("#start-date").value || null,
    language:     $("#language").value,
  };

  try {
    const resp = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      let msg = `Server error (${resp.status})`;
      try { const j = await resp.json(); msg = j.detail || j.error || msg; } catch(_) {}
      throw new Error(msg);
    }
    const { job_id } = await resp.json();
    history.replaceState(null, "", `?job=${job_id}`);
    await connectSSE(job_id);
  } catch (err) {
    console.error(err);
    showError(err.message);
    resetForm();
  }
});

function showError(msg) {
  progressSection.classList.add("hidden");
  resultsSection.classList.remove("hidden");
  resultsSection.innerHTML = `
    <div class="card">
      <div class="error-banner">
        <h3>⚠️ Generation failed</h3>
        <p>${esc(msg)}</p>
        <button onclick="location.reload()" class="btn-primary" style="width:auto;margin-top:12px;padding:10px 18px;font-size:14px">Try again</button>
      </div>
    </div>`;
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---- results ---- */
async function loadAndRenderResults(jobId) {
  const r = await fetch(`/api/jobs/${jobId}`);
  const j = await r.json();
  renderResults(jobId, j);
  resetForm();
}

function platformBadge(p) {
  const pl = (p || "").toLowerCase();
  let cls = "";
  if (pl.includes("youtube") || pl === "pw" || pl === "vedantu" || pl === "unacademy") cls = "youtube";
  else if (pl.includes("khan")) cls = "khanacademy";
  else if (pl.includes("nptel")) cls = "nptel";
  else if (pl === "pw" || pl.includes("physicswallah")) cls = "pw";
  else if (pl.includes("vedantu")) cls = "vedantu";
  else if (pl.includes("unacademy")) cls = "unacademy";
  return cls ? `platform-badge ${cls}` : "platform-badge";
}

function resourceIcon(p) {
  const pl = (p || "").toLowerCase();
  if (pl.includes("youtube") || pl === "pw" || pl === "vedantu" || pl === "unacademy" || pl.includes("mohit") || pl.includes("eduniti")) return "▶️";
  if (pl.includes("khan")) return "🎓";
  if (pl.includes("nptel")) return "🎥";
  return "📚";
}

/* ---------- Honest paid course recommendations (no sponsorships, researched from topper reviews) ---------- */
function getPaidRecommendations(examName) {
  const e = (examName||"").toLowerCase();
  const recs = [];
  if (/jee|engineering entrance|bitsat|wbjee|mhtcet|vit|srm/.test(e)) {
    recs.push({
      name: "Physics Wallah — Arjuna / Lakshya Batch (JEE)",
      teacher: "Alakh Pandey & team (PW)",
      price: "~₹4,200 per year (1/10th of Kota)",
      why: "Best value-for-money in India today. Same Alakh Pandey style as free YouTube but adds daily DPPs, weekly tests, live doubt sessions, batch community, and structured schedule. Consistently produces JEE Main/Advanced selections at a price every middle-class family can afford.",
      url: "https://www.pw.live/study/batches",
    });
    recs.push({
      name: "Alternative: Unacademy Plus (if you need specific teacher)",
      teacher: "Choose your teacher (Namo Kaul, Piyush Maheshwari etc.)",
      price: "~₹30,000 per year (expensive)",
      why: "Good if you bond with a specific teacher and can afford it. Lets you pick individual teachers per subject. Overpriced for most students compared to PW.",
      url: "https://unacademy.com/goal/jee-main-and-advanced-preparation/TMUVD",
    });
  }
  if (/neet|medical|aiims/.test(e)) {
    recs.push({
      name: "Physics Wallah — Yakeen / Lakshya NEET Batch",
      teacher: "PW (Alakh Pandey, Sarvesh Sir, Neela Bakore tutors)",
      price: "~₹4,500 per year",
      why: "Same budget-winning formula: daily lectures, DPPs with solutions, weekly tests, personal doubt support, NEET-focused content. Dozens of students get into AIIMS/Govt medical colleges from these batches every year.",
      url: "https://www.pw.live/study/batches",
    });
  }
  if (/upsc|civil services|ias/.test(e)) {
    recs.push({
      name: "FREE is genuinely best for UPSC — don't pay",
      teacher: "Mrunal Patel (Economy), Study IQ, OnlyIAS, Vision IAS free YT",
      price: "₹0 (buy only monthly current-affairs magazine ~₹80)",
      why: "90% of UPSC toppers study from free sources (NCERT + Mrunal + The Hindu + PYQs). Coachings charge ₹1-2 lakh for the same NCERT content and have a myth of 'mentorship'. We strongly recommend NOT paying for UPSC coaching; use our plan, free videos above, and self-study. If you MUST have test series, Vision IAS PT test series (~₹8,000) is the gold standard.",
      url: "https://www.youtube.com/@mrunalpatel.org",
    });
  }
  if (/ssc|bank|railway|cgl|chsl|ibps|rrb|po|clerical/.test(e)) {
    recs.push({
      name: "Adda247 Mahapack (SSC/Bank/Railway)",
      teacher: "Adda247 faculty team",
      price: "~₹2,000–₹5,000 for 1-2 years",
      why: "Best mock-test series and topic-wise question banks for govt exams. Free YouTube content is good for concepts but their paid mocks replicate the actual exam interface and give you all-India rank — essential for these speed-based exams.",
      url: "https://www.adda247.com/maha_pack",
    });
  }
  if (/nda|cds|defence/.test(e)) {
    recs.push({
      name: "Defence Wallah (PW) NDA Batch",
      teacher: "PW Defence team",
      price: "~₹3,500",
      why: "Covers Maths, GAT, English for NDA/CDS with SSB guidance. Best budget option.",
      url: "https://www.pw.live/defence",
    });
  }
  if (/ctet|tet|teaching/.test(e)) {
    recs.push({
      name: "Himanshi Singh (Let's LEARN) — CTET Paid Batch",
      teacher: "Himanshi Singh",
      price: "~₹1,500",
      why: "Himanshi Ma'am is the #1 CTET teacher in India. Her free YouTube is already enough for many; paid batch adds mock tests and doubt support.",
      url: "https://www.youtube.com/@LetsLEARN2016",
    });
  }
  if (/bpsc|uppsc|mpsc|ras|gpsc|state psc|uppcs|bihar psc/.test(e)) {
    recs.push({
      name: "FREE YouTube (Khan Sir, Study IQ, OnlyIAS) + state-specific PYQ book",
      teacher: "Khan Sir (GS), Study IQ, OnlyIAS, Utkarsh Classes",
      price: "₹0 (optional: Utkarsh/Chronicle state-specific notes ~₹500)",
      why: "State PSCs are NCERT-heavy; free YouTube + NCERT + our plan covers pre + mains for most students. Paid coaching is often a waste in Patna/Lucknow — if you want test series, pick the most popular local institute's mocks (~₹2,000).",
      url: "https://www.youtube.com/@khangsresearchcentre1685",
    });
  }
  if (/class 10|class 12|cbse|bseb|up board|icse|isc|board exam/.test(e)) {
    recs.push({
      name: "Magnet Brains + Exam Fear + our AI — FREE is enough for 90%+",
      teacher: "Magnet Brains (all subjects, Hindi+English)",
      price: "₹0",
      why: "Class 10/12 boards reward NCERT mastery + PYQ practice. Magnet Brains covers every NCERT chapter line-by-line for free. Pair with our notes + the previous 5-year CBSE/BSEB/UP paper books (~₹200 each on Amazon) and you will score 90%+ without spending a rupee.",
      url: "https://www.youtube.com/@MagnetBrains",
    });
    if (/physics|chemistry|maths|biology|pcm|pcmb/.test(e)) {
      recs.push({
        name: "If you also target JEE/NEET alongside boards: PW Udaan/Lakshya",
        teacher: "Physics Wallah",
        price: "~₹3,500–4,200",
        why: "If you are taking Class 11/12 and preparing for competitive exams at the same time, PW batches are the best budget option and cover both boards + entrance.",
        url: "https://www.pw.live/study/batches",
      });
    }
  }
  if (/gate|bt[\.\s]?ech|m\.?tech/.test(e) && !/jee|neet/.test(e)) {
    recs.push({
      name: "GATE Wallah (PW) / Made Easy (if you can afford)",
      teacher: "PW GATE faculty or Made Easy Delhi faculty",
      price: "PW ~₹5,000 · Made Easy ~₹35,000",
      why: "PW has affordable GATE batches; Made Easy is the legacy coaching but very expensive. For core subjects, free Neso Academy/Gate Smashers videos + our notes + previous 15-year GATE papers will get you a good rank if you are self-motivated.",
      url: "https://www.pw.live/gate-cse",
    });
  }
  if (/mbbs|medical college|anatomy|physiology|biochemistry/.test(e)) {
    recs.push({
      name: "PW MedEd MBBS Batch + Marrow/Prepladder",
      teacher: "Rajesh Kaushal (Anatomy), Dr. Najeeb (concepts)",
      price: "PW MedEd ~₹4,000 · Marrow/Prepladder ~₹30,000/year (for NEET-PG)",
      why: "For MBBS 1st year, Dr. Najeeb's free lectures on YouTube are legendary. Marrow/Prepladder are required for NEET-PG preparation but NOT for 1st year university exams — stick to free lectures, our notes, and your standard textbooks (Gray's, Guyton, Harper, Robbins).",
      url: "https://www.youtube.com/@DrNajeebLectures",
    });
  }
  if (!recs.length) {
    // Generic advice
    recs.push({
      name: "Free resources first (always)",
      teacher: "YouTube educators on this page",
      price: "₹0",
      why: "Always start with the free resources above. Self-study with good free videos, our AI tutor, and NCERT/textbooks beats paid coaching for most exams. Pay for a course ONLY if you need structured live classes + mock tests + doubt support AND have tried free for 1-2 weeks.",
      url: "#",
    });
  }
  return recs.slice(0, 2); // max 2 recs to not overwhelm
}

function renderResults(jobId, j) {
  if (j.error) { showError(j.error); return; }
  const pkg = j.package;
  if (!pkg) {
    resultsSection.innerHTML = `<div class="card"><p class="hint">No results yet. Status: ${esc(j.status)}</p></div>`;
    resultsSection.classList.remove("hidden");
    return;
  }
  progressSection.classList.add("hidden");

  const planUrl  = `${location.origin}/plan/${jobId}`;
  const printUrl = `${location.origin}/plan/${jobId}/print`;
  const PROGRESS_KEY = `examm_done_${jobId}`;
  const completed = new Set(JSON.parse(localStorage.getItem(PROGRESS_KEY) || "[]"));
  const doneCount = [...completed].filter(d => parseInt(d) <= pkg.total_days).length;
  const pct = pkg.total_days ? Math.round(doneCount / pkg.total_days * 100) : 0;

  const stats = [
    { n: pkg.total_chapters,       l: "Chapters" },
    { n: pkg.total_days,           l: "Days" },
    { n: Math.round(pkg.total_hours) + "h", l: "Hours" },
    { n: pkg.resources.length,     l: "Videos" },
    { n: pkg.flashcards.length,    l: "Flashcards" },
    { n: pkg.mcqs.length,          l: "MCQs" },
  ];
  const statsHtml = stats.map(s =>
    `<div class="result-stat"><div class="n">${s.n}</div><div class="l">${s.l}</div></div>`
  ).join("");

  const TABS = [
    { id: "overview",   label: "📊 Overview" },
    { id: "dashboard",  label: "📈 Dashboard" },
    { id: "plan",       label: "📅 Daily Plan" },
    { id: "resources",  label: "🎬 Resources" },
    { id: "notes",      label: "📝 Notes" },
    { id: "flashcards", label: "🗂️ Flashcards" },
    { id: "review",     label: "🔁 Review" },
    { id: "mcqs",       label: "✅ Practice MCQs" },
  ];
  const tabsHtml = TABS.map((t, i) =>
    `<button class="tab ${i===0?"active":""}" data-tab="${t.id}">${t.label}</button>`
  ).join("");

  /* ---------- Overview tab ---------- */
  const overviewHtml = `
    <div class="overview-card">
      <h3>🎉 Your personalized study package is ready!</h3>
      <p>Your plan is complete with day-by-day schedule, curated video lectures from top Indian educators, formula-dense revision notes (with beautiful math formatting), active-recall flashcards, and exam-style MCQs. Share with friends, download as PDF, or start studying right here. Your day-checkmark progress is auto-saved in this browser.</p>
    </div>
    <div class="action-row">
      <button id="copy-link" class="btn-accent">🔗 Copy shareable link</button>
      <a href="${planUrl}"  target="_blank" rel="noopener" class="btn-ghost">📖 Open share page</a>
      <a href="${printUrl}" target="_blank" rel="noopener" class="btn-ghost">📄 Download / Print PDF</a>
      <a href="https://wa.me/?text=${encodeURIComponent('📚 I made my personalized study plan on Exam Mitra for ' + pkg.exam + ' — check it out: ' + planUrl)}" target="_blank" rel="noopener" class="btn-ghost wa-btn">💬 Share on WhatsApp</a>
    </div>
    <div id="streak-bar" class="streak-bar"></div>
    <div style="margin-top:12px; display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
      <div id="pomo-widget" class="pomo-widget"></div>
      <button id="ask-tutor-top" class="btn-ghost" style="padding:8px 14px;">🤖 Ask AI Tutor about this plan</button>
      <span class="kbd-hint" title="Keyboard shortcuts">press <b>?</b> for shortcuts</span>
    </div>
    <div class="exam-pill">📘 ${esc(pkg.exam)}</div>
    <div class="progress-block" style="margin-top:14px">
      <div class="progress-block-lbl">
        <b>📊 Your study progress</b>
        <span>${doneCount}/${pkg.total_days} days completed (${pct}%)</span>
      </div>
      <div class="progress-bar"><div id="overview-progress-bar" style="width:${pct}%"></div></div>
      <p style="font-size:12px;color:var(--muted);margin:8px 0 0">Check off days in the Daily Plan tab as you finish them. Click any day to see detailed activities + direct video links.</p>
    </div>`;

  /* ---------- Daily plan (expandable with resource quick links) ---------- */
  const planHeaderHtml = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px">
      <span id="plan-progress-stat" style="font-size:13px;color:var(--muted)">
        <b style="color:var(--text)">${doneCount}/${pkg.total_days} days</b> completed (${pct}%) · Click any day to see detailed activities + quick video links
      </span>
      <button id="reset-progress" class="btn-ghost" style="padding:5px 12px;font-size:12px">Reset progress</button>
    </div>`;

  const planDaysHtml = pkg.daily_plan.map(d => {
    const isDone   = completed.has(String(d.day));
    const isReview = ((d.activities||[]).join(" ").toLowerCase().includes("revis") ||
                     d.chapter.toLowerCase().includes("revis"));
    // find up to 3 resources matching this day's chapter
    const dayRes = resourcesForDay(d.chapter, pkg.resources);
    const resLinksHtml = dayRes.length ? `
      <div class="day-chapter-label">🎬 Quick video links for this topic:</div>
      <div class="day-quick-resources">
        ${dayRes.map(r => `<a class="day-res-link" href="${esc(r.url)}" target="_blank" rel="noopener">▶️ ${esc((r.teacher_or_channel || "Lecture").slice(0,22))}: ${esc(r.title.slice(0,48))}${r.title.length>48?"…":""}</a>`).join("")}
      </div>` : "";
    return `
      <div class="day-row ${isReview?"review":""} ${isDone?"day-done":""}" data-day="${d.day}">
        <label class="day-check" title="Mark as completed" onclick="event.stopPropagation()">
          <input type="checkbox" class="day-checkbox" data-day="${d.day}" ${isDone?"checked":""}>
          <span class="checkmark"></span>
        </label>
        <div class="day-badge">D${d.day}${d.date?`<small>${d.date.slice(5)}</small>`:""}</div>
        <div class="day-body" onclick="this.closest('.day-row').classList.toggle('expanded')">
          <h4>${esc(d.chapter)}<span class="expand-icon">▼</span></h4>
          <div class="hours">${d.hours} hours · ${(d.activities||[]).length} activities · <span class="tap-hint">tap to expand</span></div>
        </div>
        <div class="day-details">
          <div class="day-detail-inner">
            <div class="day-chapter-label">📝 Today's activities in detail:</div>
            <ul style="margin:0;padding-left:20px;font-size:13.5px;color:var(--text-2)">
              ${(d.activities||[]).map(a=>`<li style="margin:6px 0;line-height:1.55">${esc(a)}</li>`).join("")}
            </ul>
            ${resLinksHtml}
          </div>
        </div>
      </div>`;
  }).join("");

  /* ---------- Resources (grouped by chapter, all open in new tab) ---------- */
  const rByCh = {};
  (pkg.resources||[]).forEach(r => { (rByCh[r.chapter] = rByCh[r.chapter]||[]).push(r); });
  const paidRecs = getPaidRecommendations(pkg.exam);
  const paidRecsHtml = paidRecs.length ? `
    <div class="paid-recs-card">
      <div class="paid-recs-head">
        <h4>💰 Optional structured courses (not required)</h4>
        <p>All AI features, notes, MCQs, flashcards and free YouTube resources above are <b>FREE forever</b>. If you want live classes, DPP sheets, weekly tests, or personal doubt support, here is our honest recommendation — researched from actual topper reviews, not paid sponsorships:</p>
      </div>
      ${paidRecs.map(p => `
        <div class="paid-rec">
          <div class="paid-rec-title">
            ${esc(p.name)}
            <span class="paid-rec-price">${esc(p.price)}</span>
          </div>
          <div class="paid-rec-teacher">${esc(p.teacher)}</div>
          <div class="paid-rec-why">${esc(p.why)}</div>
          <a class="paid-rec-link" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">Learn more ↗</a>
        </div>`).join("")}
      <p class="paid-recs-footnote">⚠️ Exam Mitra is <b>not affiliated</b> with any of these courses. Links are for information only. If your budget is tight, the free YouTube resources above + our AI tutor are enough to crack any exam — don't let anyone pressure you into paying.</p>
    </div>` : "";
  const resourcesHtml = Object.keys(rByCh).length
    ? Object.entries(rByCh).map(([ch, rs]) => `
        <h4 style="margin:20px 0 10px;font-size:15px">${esc(ch)}</h4>
        ${rs.map(r => `
          <a class="resource-card" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">
            <div class="resource-icon">${resourceIcon(r.platform)}</div>
            <div class="resource-body">
              <div class="resource-title">${esc(r.title)}</div>
              <div class="resource-meta">
                <span class="${platformBadge(r.platform)}">${esc(r.platform || "video")}</span>
                ${r.teacher_or_channel ? esc(r.teacher_or_channel) : ""}
              </div>
              ${r.why ? `<div class="resource-why">${esc(r.why)}</div>` : ""}
            </div>
            <div style="align-self:center;color:var(--indigo-500);font-weight:700;font-size:18px">↗</div>
          </a>`).join("")}`).join("") + paidRecsHtml
    : `<p class="hint">No resources found for this topic.</p>` + paidRecsHtml;

  /* ---------- Notes ---------- */
  const notesHtml = (pkg.notes||[]).length
    ? (pkg.notes||[]).map(n => `
        <div class="chapter-card">
          <div class="chapter-title">📝 ${esc(n.chapter || "Chapter Notes")}</div>
          <div class="chapter-body">
            ${(n.key_concepts||[]).length ? `<span class="section-label">Key concepts</span><ul>${n.key_concepts.map(k=>`<li>${k}</li>`).join("")}</ul>` : ""}
            ${(n.formulas_or_definitions||[]).length ? `<span class="section-label">Formulas / definitions</span>${n.formulas_or_definitions.map(f=>`<div class="formula-item">${f}</div>`).join("")}` : ""}
            ${(n.common_mistakes||[]).length ? `<span class="section-label">⚠️ Common mistakes to avoid</span>${n.common_mistakes.map(m=>`<div class="mistake-item">${esc(m)}</div>`).join("")}` : ""}
            ${n.summary ? `<span class="section-label">Exam summary</span><div class="summary-box">${n.summary}</div>` : ""}
          </div>
        </div>`).join("")
    : `<p class="hint">No notes generated.</p>`;

  /* ---------- Dashboard: weak-area radar + mastery stats ---------- */
  // Initialize SR/accuracy stores
  if (typeof ensureSRInitialized !== "undefined") ensureSRInitialized(jobId, pkg.flashcards || []);
  const dashData = (typeof buildDashboardStats === "function") ? buildDashboardStats(jobId, pkg) : null;

  const dashboardHtml = dashData ? `
    <div class="dashboard-wrap">
      <div class="dash-stats-row">
        <div class="dash-stat-card accent-indigo">
          <div class="dash-stat-num">${dashData.dueToday}</div>
          <div class="dash-stat-lbl">🔁 Cards due today</div>
        </div>
        <div class="dash-stat-card accent-emerald">
          <div class="dash-stat-num">${dashData.totalMcqCorrect}/${dashData.totalMcq}</div>
          <div class="dash-stat-lbl">✅ MCQs attempted</div>
        </div>
        <div class="dash-stat-card accent-amber">
          <div class="dash-stat-num">${Math.round(dashData.totalMcq ? (dashData.totalMcqCorrect/dashData.totalMcq*100) : 0)}%</div>
          <div class="dash-stat-lbl">🎯 Overall accuracy</div>
        </div>
        <div class="dash-stat-card accent-pink">
          <div class="dash-stat-num">${dashData.totalMastered}/${dashData.totalCards}</div>
          <div class="dash-stat-lbl">🗂️ Cards mastered</div>
        </div>
      </div>
      <div class="dash-radar-wrap">
        <h3 style="margin:0 0 8px;font-size:15px">📊 Chapter mastery radar</h3>
        <p class="hint" style="margin:0 0 10px">Updates live as you answer MCQs and review flashcards. Aim for green across the board.</p>
        <div id="radar-container">${radarChart(dashData.stats, 340)}</div>
      </div>
      ${dashData.weakChapters.length ? `
      <div class="dash-weak-wrap">
        <h3 style="margin:20px 0 8px;font-size:15px;color:var(--error)">⚠️ Chapters to revisit</h3>
        ${dashData.weakChapters.map(c => `
          <div class="dash-weak-item">
            <div><b>${esc(c.label)}</b> — ${Math.round(c.mcqAcc*100)}% accuracy on ${c.mcqTotal} MCQs</div>
            <button class="btn-ghost" onclick="(()=>{document.querySelector('.tab[data-tab=\\'plan\\']').click();})()">Review in plan →</button>
          </div>`).join("")}
      </div>` : `<div class="dash-weak-wrap"><p style="color:var(--success);font-weight:600">🌟 No weak chapters detected yet! Answer some MCQs to see your mastery.</p></div>`}
    </div>` : `<p class="hint">Loading dashboard…</p>`;

  /* ---------- Flashcards ---------- */
  const cardsHtml = `
    <p class="hint" style="margin-top:0">👆 Click any card to flip and reveal the answer. Formulas render beautifully! Rate cards 1-5 when reviewing in the 🔁 Review tab.</p>
    <div class="flashcard-grid">
      ${(pkg.flashcards||[]).map((c, idx) => `
        <div class="flashcard" data-fc-idx="${idx}">
          <div class="flashcard-inner">
            <div class="flashcard-front">
              <span class="flashcard-tag">${esc(c.difficulty || "medium")}</span>
              <div>${c.front}</div>
              <div class="flashcard-hint">Click to flip</div>
            </div>
            <div class="flashcard-back">
              <span class="flashcard-tag">answer</span>
              <div>${c.back}</div>
            </div>
          </div>
        </div>`).join("")}
    </div>`;

  /* ---------- Spaced Repetition Review tab ---------- */
  const reviewCards = (typeof getDueCards === "function") ? getDueCards(jobId) : [];
  const reviewHtml = `
    <div class="review-wrap">
      <div class="review-header">
        <h3 style="margin:0">🔁 Spaced-Repetition Review</h3>
        <p class="hint" style="margin:4px 0 0">Based on the SM-2 algorithm (SuperMemo 2). Rate each card honestly after seeing the answer. Cards you forget come back tomorrow; easy ones return in days/weeks. This is how toppers build long-term memory.</p>
      </div>
      <div id="review-queue-info" class="review-queue-info">
        ${reviewCards.length ? `🔔 <b>${reviewCards.length}</b> card${reviewCards.length===1?"":"s"} due today` : `🎉 <b>0</b> cards due — great job! Come back tomorrow, or click any card in the Flashcards tab to start practicing.`}
      </div>
      <div id="review-card-container"></div>
      <div id="review-done-msg" style="display:none;text-align:center;padding:30px">
        <div style="font-size:48px">🎉</div>
        <h3>All cards reviewed for today!</h3>
        <p style="color:var(--muted)">Come back tomorrow for more. Your memory is being optimized by spaced repetition.</p>
      </div>
    </div>`;

  /* ---------- MCQs ---------- */
  const mcqsHtml = `
    <p class="hint" style="margin-top:0">Select an answer for each question, then click <b>Grade my answers</b> to see your score, explanations, and weak areas. Your accuracy per chapter feeds the 📈 Dashboard.</p>
    <div id="mcq-list">
      ${(pkg.mcqs||[]).map((q,i) => `
        <div class="mcq" data-idx="${i}" data-correct="${esc(q.correct_answer)}" data-chapter="${esc(q.chapter)}">
          <div class="mcq-q"><b>Q${i+1}.</b> ${q.question}
            <small>${esc(q.chapter)} · ${esc(q.difficulty)}</small>
          </div>
          <div class="mcq-options">
            ${(q.options||[]).map(o => `
              <div class="mcq-option" data-label="${esc(o.label)}">
                <span class="letter">${esc(o.label)}</span>
                <span>${o.text}</span>
              </div>`).join("")}
          </div>
          <div class="mcq-explanation"><b>Explanation:</b> ${q.explanation}</div>
        </div>`).join("")}
    </div>
    <button id="grade-btn" class="btn-accent" style="margin-top:14px;padding:12px 24px;font-size:14px">📊 Grade my answers</button>
    <div id="grade-result"></div>`;

  /* ---------- Assemble ---------- */
  resultsSection.innerHTML = `<div class="card">
    <div class="result-header">
      <h2>✅ Your personalized study plan</h2>
      <p>Built autonomously by Exam Mitra's 9 AI agents · ${esc(pkg.exam)}</p>
      <div class="result-stats">${statsHtml}</div>
    </div>
    <div class="tabs">${tabsHtml}</div>
    <div class="tab-panel active" data-panel="overview">${overviewHtml}</div>
    <div class="tab-panel" data-panel="dashboard">${dashboardHtml}</div>
    <div class="tab-panel" data-panel="plan">${planHeaderHtml}${planDaysHtml}</div>
    <div class="tab-panel" data-panel="resources">${resourcesHtml}</div>
    <div class="tab-panel" data-panel="notes">${notesHtml}</div>
    <div class="tab-panel" data-panel="flashcards">${cardsHtml}</div>
    <div class="tab-panel" data-panel="review">${reviewHtml}</div>
    <div class="tab-panel" data-panel="mcqs">${mcqsHtml}</div>
  </div>`;
  resultsSection.classList.remove("hidden");

  // Render KaTeX math in results
  renderMathIn(resultsSection);

  wireUpResultInteractions(jobId, pkg, PROGRESS_KEY, completed, pkg.total_days, planUrl);

  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---- Wire up all interactive bits inside the rendered results ---- */
function wireUpResultInteractions(jobId, pkg, PROGRESS_KEY, completed, totalDays, planUrl) {
  const root = resultsSection;

  /* Tab switching */
  $$(".tab", root).forEach(tab => {
    tab.addEventListener("click", () => {
      $$(".tab", root).forEach(x => x.classList.remove("active"));
      $$(".tab-panel", root).forEach(x => x.classList.remove("active"));
      tab.classList.add("active");
      const panel = root.querySelector(`[data-panel="${tab.dataset.tab}"]`);
      if (panel) {
        panel.classList.add("active");
        // (re)render math in newly revealed panel
        renderMathIn(panel);
      }
    });
  });

  /* Copy link */
  $("#copy-link", root)?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(planUrl);
      toast("✅ Link copied to clipboard!");
    } catch(e) {
      // Fallback
      const ta = document.createElement("textarea");
      ta.value = planUrl;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); toast("✅ Link copied!"); }
      catch(_) { alert("Copy this link: " + planUrl); }
      document.body.removeChild(ta);
    }
  });

  /* Flashcard flip */
  root.addEventListener("click", e => {
    const fc = e.target.closest(".flashcard");
    if (fc && !e.target.closest("a")) fc.classList.toggle("flipped");
  });

  /* Day checkboxes */
  let prevDone = [...completed].length;
  const updateProgress = () => {
    const done = $$(".day-checkbox:checked", root).length;
    const pct = Math.round(done / totalDays * 100);
    const bar = $("#overview-progress-bar", root);
    if (bar) bar.style.width = pct + "%";
    const stat = $("#plan-progress-stat", root);
    if (stat) stat.innerHTML = `<b style="color:var(--text)">${done}/${totalDays} days</b> completed (${pct}%) · Click any day to see detailed activities + quick video links`;
    $$(".day-checkbox", root).forEach(cb => {
      cb.closest(".day-row").classList.toggle("day-done", cb.checked);
      cb.checked ? completed.add(cb.dataset.day) : completed.delete(cb.dataset.day);
    });
    localStorage.setItem(PROGRESS_KEY, JSON.stringify([...completed]));
    // Celebrate when a new day is checked off
    if (done > prevDone) {
      bumpStreak("task");
      if (done === totalDays) { fireConfetti(2600); toast("🎉 All days complete! You're on fire — take a screenshot and share with friends!"); }
      else fireConfetti(700);
    }
    prevDone = done;
  };
  $$(".day-checkbox", root).forEach(cb => cb.addEventListener("change", updateProgress));

  $("#reset-progress", root)?.addEventListener("click", () => {
    if (!confirm("Reset all day checkmarks for this plan?")) return;
    completed.clear();
    localStorage.removeItem(PROGRESS_KEY);
    $$(".day-checkbox", root).forEach(cb => { cb.checked = false; });
    $$(".day-row", root).forEach(r => r.classList.remove("day-done"));
    updateProgress();
    toast("Progress reset");
  });

  /* MCQ selection + grading */
  $$(".mcq", root).forEach(mcq => {
    $$(".mcq-option", mcq).forEach(opt => {
      opt.addEventListener("click", () => {
        if (mcq.classList.contains("explained")) return;
        $$(".mcq-option", mcq).forEach(o => o.classList.remove("selected"));
        opt.classList.add("selected");
      });
    });
  });

  $("#grade-btn", root)?.addEventListener("click", async () => {
    const answers = {};
    $$(".mcq", root).forEach(mcq => {
      const sel = $(".mcq-option.selected", mcq);
      if (sel) answers[mcq.dataset.idx] = sel.dataset.label;
    });
    const btn = $("#grade-btn", root);
    btn.disabled = true; btn.textContent = "Grading…";
    try {
      const resp = await fetch(`/api/jobs/${jobId}/grade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
      });
      if (!resp.ok) throw new Error("Grade failed");
      const r = await resp.json();
      $$(".mcq", root).forEach(mcq => {
        const correct = mcq.dataset.correct;
        const picked  = answers[mcq.dataset.idx];
        const chapter = mcq.dataset.chapter || "";
        const isCorrect = picked === correct;
        mcq.classList.add("explained");
        $$(".mcq-option", mcq).forEach(o => {
          o.classList.add("locked");
          if (o.dataset.label === correct) o.classList.add("correct");
          if (o.dataset.label === picked && picked !== correct) o.classList.add("wrong");
        });
        // Record per-chapter accuracy for dashboard
        if (typeof recordMCQResult === "function" && chapter) {
          recordMCQResult(jobId, chapter, isCorrect);
        }
        // Re-render math in explanation
        renderMathIn(mcq.querySelector(".mcq-explanation"));
      });
      refreshDashboard && refreshDashboard();
      const weakHtml = (r.weak_areas||[]).length
        ? `<h4 style="margin:12px 0 6px">📌 Areas to revisit:</h4>
           <ul class="weak-list">${r.weak_areas.map(w =>
             `<li><b>${esc(w.chapter)}</b> — ${esc(w.topic)}: ${esc(w.feedback)}</li>`
           ).join("")}</ul>`
        : `<p style="margin:10px 0 0;color:var(--success);font-weight:600">🌟 Perfect score — excellent work!</p>`;
      $("#grade-result", root).innerHTML = `
        <div class="grade-result">
          <div class="grade-score">🎯 ${r.score}/${r.total} (${r.percentage.toFixed(0)}%)</div>
          <p class="grade-msg">${esc(r.encouragement)}</p>
          ${weakHtml}
        </div>`;
      renderMathIn($("#grade-result", root));
      // Adaptive remediation: offer booster pack if there are weak areas
      if (r.weak_areas && r.weak_areas.length) {
        requestRemediation(jobId, r.score, r.total, r.weak_areas, root);
      } else if (r.percentage === 100) {
        fireConfetti(2200);
      }
    } catch(e) {
      toast("Grading error: " + e.message);
    }
    btn.disabled = false;
    btn.textContent = "📊 Grade my answers";
  });

  /* Dashboard refresher — re-renders radar + stats after grading */
  function refreshDashboard() {
    if (typeof buildDashboardStats !== "function") return;
    const d = buildDashboardStats(jobId, pkg);
    const container = document.getElementById("radar-container");
    if (container) container.innerHTML = radarChart(d.stats, 340);
    renderMathIn(container);
    // Re-render stats cards
    document.querySelectorAll(".dash-stat-card").forEach((el, i) => {
      const nums = [d.dueToday, `${d.totalMcqCorrect}/${d.totalMcq}`, `${Math.round(d.totalMcq ? (d.totalMcqCorrect/d.totalMcq*100) : 0)}%`, `${d.totalMastered}/${d.totalCards}`];
      el.querySelector(".dash-stat-num").textContent = nums[i] || "0";
    });
  }

  /* Spaced-repetition review flow */
  let reviewQueue = (typeof getDueCards === "function") ? getDueCards(jobId) : [];
  let reviewIdx = 0;
  function showNextReviewCard() {
    const container = document.getElementById("review-card-container");
    const doneMsg = document.getElementById("review-done-msg");
    const info = document.getElementById("review-queue-info");
    if (!container) return;
    if (reviewIdx >= reviewQueue.length) {
      container.innerHTML = "";
      if (doneMsg) doneMsg.style.display = "block";
      if (info) info.innerHTML = `🎉 <b>All done!</b> Reviewed ${reviewQueue.length} card${reviewQueue.length===1?"":"s"}. Come back tomorrow for your next session.`;
      fireConfetti(1600);
      refreshDashboard();
      return;
    }
    const card = reviewQueue[reviewIdx];
    container.innerHTML = `
      <div class="review-card">
        <div class="review-progress">Card ${reviewIdx+1} of ${reviewQueue.length}</div>
        <div class="review-chapter">${esc(card.chapter || "")}</div>
        <div class="review-question" id="review-question">${card.front}</div>
        <div class="review-answer-wrap" id="review-answer-wrap" style="display:none">
          <div class="review-answer-divider"></div>
          <div class="review-answer" id="review-answer">${card.back}</div>
          <div class="review-rate-label">How well did you remember?</div>
          <div class="review-rate-buttons">
            <button class="rate-btn rate-1" data-rating="1" title="Total blackout">😖 Forgot</button>
            <button class="rate-btn rate-2" data-rating="2" title="Wrong but familiar">😕 Hard</button>
            <button class="rate-btn rate-3" data-rating="3" title="Correct with effort">🤔 Okay</button>
            <button class="rate-btn rate-4" data-rating="4" title="Correct, some hesitation">🙂 Good</button>
            <button class="rate-btn rate-5" data-rating="5" title="Perfect, instant recall">😎 Easy</button>
          </div>
        </div>
        <button id="review-show-btn" class="btn-accent">👁️ Show answer</button>
      </div>`;
    renderMathIn(container);
    const showBtn = document.getElementById("review-show-btn");
    showBtn?.addEventListener("click", () => {
      document.getElementById("review-answer-wrap").style.display = "block";
      showBtn.style.display = "none";
      renderMathIn(document.getElementById("review-answer-wrap"));
    });
    container.querySelectorAll(".rate-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const rating = parseInt(btn.dataset.rating);
        const sr = loadSR(jobId);
        const cardId = card.id;
        if (sr[cardId]) applyRating(sr[cardId], rating);
        saveSR(jobId, sr);
        reviewIdx++;
        showNextReviewCard();
      });
    });
  }
  // Start review on first open of the Review tab
  const reviewPanel = root.querySelector('[data-panel="review"]');
  if (reviewPanel) {
    const reviewTab = root.querySelector('.tab[data-tab="review"]');
    reviewTab?.addEventListener("click", () => {
      reviewQueue = (typeof getDueCards === "function") ? getDueCards(jobId) : [];
      reviewIdx = 0;
      const doneMsg = document.getElementById("review-done-msg");
      if (doneMsg) doneMsg.style.display = "none";
      setTimeout(showNextReviewCard, 100);
    });
    // Auto-start if there are due cards and this is first render
    // (don't auto-switch tabs; user opens it on their own)
  }

  /* Tutor top button */
  $("#ask-tutor-top", root)?.addEventListener("click", () => {
    const firstChapter = (pkg.notes && pkg.notes[0]) ? pkg.notes[0].chapter : "";
    ensureTutorDOMElements();
    openTutor(jobId, firstChapter);
  });

  /* Pomodoro */
  renderPomo();

  /* Streak */
  bumpStreak("plan");
  renderStreak();

  /* Confetti celebration on first render */
  setTimeout(() => fireConfetti(1400), 400);

  /* Add voice buttons next to formulas? Keep simple: add speaker to key concepts */
  $$(".note-section h4, .formula-item", root).forEach(el => {
    if (el.querySelector(".speak-btn")) return;
    const b = document.createElement("button");
    b.className = "speak-btn";
    b.innerHTML = "🔊";
    b.title = "Read this aloud";
    b.addEventListener("click", (ev) => { ev.stopPropagation(); speakText(el.innerText.replace(/🔊/g,"")); });
    el.appendChild(b);
  });
}

/* Lazily inject the floating Tutor FAB + panel once per page load */
let tutorDOMElementsInjected = false;
function ensureTutorDOMElements() {
  if (tutorDOMElementsInjected) return;
  tutorDOMElementsInjected = true;
  const fab = document.createElement("button");
  fab.className = "tutor-fab pulse";
  fab.id = "tutor-fab";
  fab.title = "Ask AI Tutor (T)";
  fab.innerHTML = "🤖";
  fab.addEventListener("click", () => {
    if (!tutorJobId) { toast("Generate a plan first, then I can tutor you on it!"); return; }
    openTutor(tutorJobId, tutorChapter);
  });
  document.body.appendChild(fab);

  const panel = document.createElement("div");
  panel.className = "tutor-panel";
  panel.id = "tutor-panel";
  panel.innerHTML = `
    <div class="tutor-head">
      <div>
        <h3>🤖 Your Exam Mitra Tutor</h3>
        <small>Ask me anything about your plan — I explain in your language with formulas.</small>
      </div>
      <button class="tutor-close" onclick="closeTutor()">✕</button>
    </div>
    <div class="tutor-body"></div>
    <div class="tutor-quick"></div>
    <div class="tutor-input-row">
      <input id="tutor-input" class="tutor-input" placeholder="Ask a doubt, e.g. Why does projectile range use sin 2θ?" />
      <button class="tutor-send" onclick="sendTutor()">Send</button>
    </div>
  `;
  document.body.appendChild(panel);

  const input = panel.querySelector("#tutor-input");
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") sendTutor(); });
}

/* ===============================================================
   Exam Mitra v2.2 — Adaptive Tutor / Pomodoro / Streak / Confetti
   =============================================================== */

/* ---------- Streak (localStorage) ---------- */
function getStreak() {
  const d = JSON.parse(localStorage.getItem("em_streak") || "{}");
  return { days: d.days || 0, last: d.last || null, totalTasks: d.totalTasks || 0, plans: d.plans || 0 };
}
function bumpStreak(kind /* "task" | "plan" */) {
  const s = getStreak();
  const today = new Date().toISOString().slice(0,10);
  if (kind === "plan") s.plans = (s.plans || 0) + 1;
  if (kind === "task") {
    s.totalTasks++;
    if (s.last === today) { /* already counted */ }
    else {
      const yest = new Date(Date.now() - 86400000).toISOString().slice(0,10);
      s.days = (s.last === yest) ? s.days + 1 : 1;
      s.last = today;
    }
  }
  localStorage.setItem("em_streak", JSON.stringify(s));
  renderStreak();
}
function renderStreak() {
  const s = getStreak();
  const el = document.getElementById("streak-bar");
  if (!el) return;
  el.innerHTML = `
    <span class="streak-badge">🔥 ${s.days} day${s.days===1?"":"s"}</span>
    <span class="streak-meta"><b>${s.plans}</b> plan${s.plans===1?"":"s"} created · <b>${s.totalTasks||0}</b> day${(s.totalTasks||0)===1?"":"s"} marked done</span>
  `;
}

/* ---------- Confetti (pure JS, zero deps) ---------- */
function fireConfetti(duration = 1800) {
  let canvas = document.getElementById("confetti-canvas");
  if (canvas) canvas.remove();
  canvas = document.createElement("canvas");
  canvas.id = "confetti-canvas";
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  document.body.appendChild(canvas);
  const ctx = canvas.getContext("2d");
  const colors = ["#6366f1","#8b5cf6","#ec4899","#f59e0b","#10b981","#06b6d4","#ef4444","#84cc16"];
  const pieces = [];
  for (let i=0;i<140;i++) pieces.push({
    x: Math.random()*canvas.width,
    y: -20 - Math.random()*200,
    r: 4+Math.random()*5,
    vx: (Math.random()-.5)*4,
    vy: 2+Math.random()*3,
    c: colors[Math.floor(Math.random()*colors.length)],
    tilt: Math.random()*Math.PI,
    spin: (Math.random()-.5)*.25,
  });
  const start = performance.now();
  function frame(t) {
    const elapsed = t - start;
    ctx.clearRect(0,0,canvas.width,canvas.height);
    pieces.forEach(p => {
      p.x += p.vx; p.y += p.vy; p.vy += .08; p.tilt += p.spin;
      ctx.save();
      ctx.translate(p.x,p.y); ctx.rotate(p.tilt);
      ctx.fillStyle = p.c;
      ctx.fillRect(-p.r/2,-p.r/2,p.r,p.r*1.6);
      ctx.restore();
    });
    if (elapsed < duration && pieces.some(p => p.y < canvas.height+20)) {
      requestAnimationFrame(frame);
    } else { canvas.remove(); }
  }
  requestAnimationFrame(frame);
}
window.addEventListener("resize", () => {
  const c = document.getElementById("confetti-canvas");
  if (c) { c.width = window.innerWidth; c.height = window.innerHeight; }
});

/* ---------- Pomodoro timer ---------- */
const POMO = {
  focus: 25*60, short: 5*60, long: 15*60,
  remaining: 25*60, mode: "focus", interval: null, cycles: 0,
};
function fmtTime(s) {
  const m = Math.floor(s/60), sec = s%60;
  return `${String(m).padStart(2,"0")}:${String(sec).padStart(2,"0")}`;
}
function renderPomo() {
  const el = document.getElementById("pomo-widget");
  if (!el) return;
  el.classList.toggle("running", !!POMO.interval && POMO.mode==="focus");
  el.classList.toggle("break", POMO.mode!=="focus");
  el.innerHTML = `
    <div>
      <div class="pomo-mode">${POMO.mode==="focus"?"🎯 Focus":"☕ Break"} · cycle ${POMO.cycles+1}</div>
      <div class="pomo-display">${fmtTime(POMO.remaining)}</div>
    </div>
    <button id="pomo-toggle">${POMO.interval?"Pause":"Start"}</button>
    <button id="pomo-reset" title="Reset">↺</button>
  `;
  document.getElementById("pomo-toggle")?.addEventListener("click", togglePomo);
  document.getElementById("pomo-reset")?.addEventListener("click", resetPomo);
}
function togglePomo() {
  if (POMO.interval) { clearInterval(POMO.interval); POMO.interval = null; renderPomo(); return; }
  POMO.interval = setInterval(() => {
    POMO.remaining--;
    if (POMO.remaining <= 0) {
      clearInterval(POMO.interval); POMO.interval = null;
      const nextMode = POMO.mode === "focus" ? (++POMO.cycles%4===0 ? "long" : "short") : "focus";
      try {
        new Audio("data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbsGM2on1/f39/f39/f39/f39/f39/f4CHi5SVmJCQk5WVn6ChpKWnp7e7ur6+vsPHx9/c4erk6uvp6+zt7e7s7Onp6OTj5efl5+bp7Ozs7e7u7+/v8PX19/b4+vr6+fr7/P3+/w==").play().catch(()=>{});
      } catch(_) {}
      if (nextMode === "focus") { fireConfetti(1400); bumpStreak("task"); toast("🎉 Pomodoro done! Take a well-deserved break."); }
      else toast("☕ Break over — time to focus!");
      POMO.mode = nextMode;
      POMO.remaining = POMO[nextMode==="long"?"long":nextMode];
    }
    renderPomo();
    if (POMO.remaining%30===0 || POMO.remaining<=10) {
      document.title = POMO.mode==="focus" ? `🎯 ${fmtTime(POMO.remaining)} — Exam Mitra` : `☕ ${fmtTime(POMO.remaining)} — Exam Mitra`;
    }
  }, 1000);
  renderPomo();
}
function resetPomo() {
  if (POMO.interval) { clearInterval(POMO.interval); POMO.interval=null; }
  POMO.mode = "focus"; POMO.remaining = POMO.focus; POMO.cycles = 0;
  document.title = "Exam Mitra 📚 — AI Study Planner for JEE, NEET, UPSC, College & All Indian Exams";
  renderPomo();
}

/* ---------- Adaptive remediation (called after grading if score < 100%) ---------- */
async function requestRemediation(jobId, score, total, weakAreas, container) {
  if (!weakAreas || !weakAreas.length) return;
  if (score === total) { fireConfetti(2200); return; }
  const pct = Math.round(score/total*100);
  const card = document.createElement("div");
  card.className = "remediation-card";
  card.innerHTML = `
    <h3>🧠 Personal tutor mode</h3>
    <p class="remediation-diagnosis">You scored <b>${score}/${total} (${pct}%)</b>. I noticed a few weak spots. Want me to build a short focused revision plan with harder MCQs targeting exactly what you got wrong?</p>
    <button class="btn-remediate" id="remediate-btn">✨ Yes — build my booster pack</button>
  `;
  container.appendChild(card);
  document.getElementById("remediate-btn").addEventListener("click", async () => {
    const btn = document.getElementById("remediate-btn");
    btn.disabled = true; btn.textContent = "Thinking like your personal tutor…";
    try {
      const r = await fetch(`/api/jobs/${jobId}/remediate`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ score, total, weak_areas: weakAreas }),
      });
      if (!r.ok) throw new Error("Tutor failed: " + r.status);
      const pkg = await r.json();
      renderRemediation(card, pkg);
    } catch(e) {
      btn.disabled = false; btn.textContent = "🔁 Try again";
      toast("Tutor error: " + e.message);
    }
  });
}
function renderRemediation(card, pkg) {
  const revisionHtml = (pkg.revision_days||[]).map(d => `
    <div class="day-row" style="background:#fff;border-radius:12px;padding:10px 12px;margin:6px 0;">
      <div class="day-badge" style="background:#10b981;color:#fff;">R${d.day||1}</div>
      <div class="day-body" style="cursor:default;">
        <h4 style="margin:0 0 4px;font-size:14px;">${esc(d.chapter)} <span style="color:var(--muted);font-weight:400;font-size:12px;">· ${d.hours}h</span></h4>
        <ul style="margin:0;padding-left:18px;font-size:12.5px;color:var(--text-2);">
          ${(d.activities||[]).map(a=>`<li>${esc(a)}</li>`).join("")}
        </ul>
      </div>
    </div>`).join("");
  const boosterHtml = (pkg.booster_notes||[]).map(n => `
    <div class="booster-note">
      <h5>🔁 ${esc(n.chapter)} — Booster notes</h5>
      ${n.summary ? `<p style="margin:0 0 8px;font-size:13px;color:#065f46;">${n.summary}</p>` : ""}
      <ul style="margin:0 0 8px;padding-left:18px;font-size:13px;">
        ${(n.key_concepts||[]).map(k=>`<li>${k}</li>`).join("")}
      </ul>
      ${(n.formulas_or_definitions||[]).length ? `<div style="display:flex;flex-direction:column;gap:6px;">
        ${n.formulas_or_definitions.map(f=>`<div class="formula-item" style="padding:8px 12px;font-size:13.5px;">${f}</div>`).join("")}
      </div>` : ""}
      ${(n.common_mistakes||[]).length ? `<div style="margin-top:8px;display:flex;flex-direction:column;gap:6px;">
        ${n.common_mistakes.map(m=>`<div class="mistake-item" style="padding:8px 12px;font-size:13px;">⚠️ ${m}</div>`).join("")}
      </div>` : ""}
    </div>`).join("");
  const extraMcqHtml = (pkg.extra_mcqs||[]).length ? `
    <div class="remediation-section-title">🎯 Harder MCQs on your weak spots</div>
    <div id="remed-mcqs">
      ${(pkg.extra_mcqs||[]).map((q,i)=>`
        <div class="mcq" data-idx="R${i}" data-correct="${esc(q.correct_answer)}">
          <div class="mcq-q"><b>Q${i+1}.</b> ${q.question}
            <button class="speak-btn" onclick="speakText(this.parentElement.innerText)">🔊</button></div>
          <div class="mcq-options">
            ${(q.options||[]).map(o=>`<div class="mcq-option" data-label="${esc(o.label)}"><b>${esc(o.label)}.</b> ${o.text}</div>`).join("")}
          </div>
          <div class="mcq-explanation"><b>Explanation:</b> ${q.explanation||""}</div>
        </div>`).join("")}
    </div>
    <button class="btn-accent" id="remed-grade-btn" style="margin-top:12px;">📊 Re-check these</button>
    <div id="remed-grade-result"></div>` : "";
  card.innerHTML = `
    <h3>🧠 Adaptive booster pack ${pkg.round?`<small style="font-weight:400;color:#047857;">· round ${pkg.round}</small>`:""}</h3>
    <p class="remediation-diagnosis">🔍 <b>Diagnosis:</b> ${esc(pkg.diagnosis||"")}</p>
    <div class="remediation-section-title">📅 Your 2-day targeted revision</div>
    ${revisionHtml}
    ${boosterHtml}
    ${extraMcqHtml}
    <p style="margin-top:14px;color:#047857;font-style:italic;font-size:13px;">💪 ${esc(pkg.motivation||"")}</p>
  `;
  // Hook up MCQ interactions for remedial MCQs
  const root2 = card;
  root2.querySelectorAll(".mcq").forEach(mcq => {
    mcq.querySelectorAll(".mcq-option").forEach(opt => {
      opt.addEventListener("click", () => {
        if (mcq.classList.contains("explained")) return;
        mcq.querySelectorAll(".mcq-option").forEach(o=>o.classList.remove("selected"));
        opt.classList.add("selected");
      });
    });
  });
  renderMathIn(card);
  const rgb = document.getElementById("remed-grade-btn");
  if (rgb) rgb.addEventListener("click", () => {
    const answers = {};
    root2.querySelectorAll(".mcq").forEach(mcq => {
      const sel = mcq.querySelector(".mcq-option.selected");
      if (sel) answers[mcq.dataset.idx] = sel.dataset.label;
    });
    let score=0, total=(pkg.extra_mcqs||[]).length;
    root2.querySelectorAll(".mcq").forEach(mcq => {
      const correct = mcq.dataset.correct;
      const picked = answers[mcq.dataset.idx];
      mcq.classList.add("explained");
      mcq.querySelectorAll(".mcq-option").forEach(o => {
        o.classList.add("locked");
        if (o.dataset.label === correct) o.classList.add("correct");
        if (o.dataset.label === picked && picked !== correct) o.classList.add("wrong");
      });
      if (picked === correct) score++;
      renderMathIn(mcq.querySelector(".mcq-explanation"));
    });
    const pct = Math.round(score/total*100);
    const res = document.getElementById("remed-grade-result");
    let msg = pct>=80 ? "🌟 Excellent! You're improving fast!" : (pct>=50 ? "👍 Good progress — re-read the booster notes above." : "📌 Don't rush. Re-read the booster notes, re-watch the video, then try again.");
    res.innerHTML = `<div class="grade-result" style="margin-top:12px;">
      <div class="grade-score">🎯 ${score}/${total} (${pct}%)</div>
      <p class="grade-msg">${msg}</p>
    </div>`;
    if (pct >= 80) fireConfetti(1600);
    else if (score < total) {
      // Another round!
      const weak = [];
      root2.querySelectorAll(".mcq").forEach(mcq => {
        const picked = answers[mcq.dataset.idx];
        if (picked !== mcq.dataset.correct) {
          weak.push({ chapter: "(remedial)", topic: mcq.querySelector(".mcq-q")?.textContent?.slice(0,80)||"topic", feedback: "Missed remedial MCQ." });
        }
      });
      if (weak.length) {
        const nextBtn = document.createElement("button");
        nextBtn.className = "btn-remediate";
        nextBtn.textContent = "🔁 One more booster round";
        nextBtn.style.marginTop = "10px";
        nextBtn.addEventListener("click", async () => {
          nextBtn.disabled = true; nextBtn.textContent = "Building harder round…";
          const r = await fetch(`/api/jobs/${jobId}/remediate`, {
            method:"POST", headers:{"Content-Type":"application/json"},
            body: JSON.stringify({ score, total, weak_areas: weakAreas.concat(weak) }),
          });
          if (!r.ok) { nextBtn.disabled=false; nextBtn.textContent="🔁 Try again"; return; }
          const p2 = await r.json();
          const newCard = document.createElement("div");
          newCard.className = "remediation-card";
          card.parentNode.insertBefore(newCard, card.nextSibling);
          renderRemediation(newCard, p2);
          nextBtn.remove();
        });
        res.appendChild(nextBtn);
      }
    }
  });
}

/* ---------- AI Tutor chat (floating) ---------- */
let tutorJobId = null;
let tutorHistory = [];
let tutorChapter = "";

function openTutor(jobId, chapterHint) {
  tutorJobId = jobId;
  tutorChapter = chapterHint || "";
  const panel = document.getElementById("tutor-panel");
  panel.classList.add("open");
  document.getElementById("tutor-fab").classList.remove("pulse");
  const body = panel.querySelector(".tutor-body");
  if (body.children.length === 0) {
    addTutorMsg("bot", `Namaste! 🙏 I'm your personal AI tutor. Ask me anything about <b>${esc(chapterHint||"your plan")}</b> — a concept, a formula, why something works, or even "solve this for me step by step". I'll explain in your language, with LaTeX math when needed.`);
    const quick = panel.querySelector(".tutor-quick");
    quick.innerHTML = [
      "Explain this concept in simple words",
      "Show me a step-by-step solved example",
      "What's the common mistake students make here?",
      "Give me a mnemonic / trick to remember this",
    ].map(q=>`<button onclick="sendTutor(\`${esc(q.replace(/`/g,"'"))}\`); this.parentElement.innerHTML='';">${esc(q)}</button>`).join("");
  }
  setTimeout(() => document.getElementById("tutor-input").focus(), 250);
}
function closeTutor() { document.getElementById("tutor-panel").classList.remove("open"); }
function addTutorMsg(who, text) {
  const body = document.querySelector("#tutor-panel .tutor-body");
  const div = document.createElement("div");
  div.className = `tutor-msg ${who}`;
  div.innerHTML = text;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
  // Render KaTeX inside tutor messages
  if (window.renderMathInElement && who === "bot") {
    renderMathInElement(div, {
      delimiters: [{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false},{left:"\\(",right:"\\)",display:false},{left:"\\[",right:"\\]",display:true}],
      throwOnError: false,
    });
  }
}
async function sendTutor(overrideText) {
  const input = document.getElementById("tutor-input");
  const q = (overrideText || input.value || "").trim();
  if (!q || !tutorJobId) return;
  if (!overrideText) input.value = "";
  addTutorMsg("user", esc(q));
  tutorHistory.push("Student: " + q);
  const typing = document.createElement("div");
  typing.className = "tutor-typing";
  typing.textContent = "Tutor is thinking…";
  document.querySelector("#tutor-panel .tutor-body").appendChild(typing);
  const sendBtn = document.querySelector(".tutor-send");
  if (sendBtn) sendBtn.disabled = true;
  try {
    const r = await fetch(`/api/jobs/${tutorJobId}/tutor`, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ question: q, chapter: tutorChapter, history: tutorHistory.slice(-6) }),
    });
    if (!r.ok) throw new Error("Tutor error " + r.status);
    const data = await r.json();
    typing.remove();
    // Render markdown-lite: bold **x**, code blocks, newlines
    let ans = data.answer
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
      .replace(/`{3}([\s\S]*?)`{3}/g, (_,c)=>`<pre>${c}</pre>`)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\n/g, "<br>");
    addTutorMsg("bot", ans);
    tutorHistory.push("Tutor: " + data.answer.replace(/\n+/g," "));
    if (tutorHistory.length > 20) tutorHistory = tutorHistory.slice(-12);
  } catch(e) {
    typing.remove();
    addTutorMsg("bot", "<i>Sorry, I couldn't answer that right now. Try again shortly.</i>");
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    input.focus();
  }
}

/* ---------- Voice read-aloud (Web Speech API, no server cost) ---------- */
function speakText(text) {
  if (!("speechSynthesis" in window)) { toast("Voice not supported in this browser."); return; }
  window.speechSynthesis.cancel();
  // Strip LaTeX for cleaner speech
  const clean = text
    .replace(/\$[^$]+\$/g, m => m.replace(/\\frac\{([^}]*)\}\{([^}]*)\}/g, "$1 over $2")
                                .replace(/\\[a-zA-Z]+/g, " ")
                                .replace(/[{}_^\\]/g," "))
    .replace(/\s+/g," ").trim();
  const u = new SpeechSynthesisUtterance(clean);
  u.rate = 1.0; u.pitch = 1.0;
  // Try to match language
  const saved = localStorage.getItem("em_lang") || "en";
  u.lang = saved === "hi" ? "hi-IN" : (saved === "hinglish" ? "hi-IN" : "en-IN");
  // Prefer Indian voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.lang === u.lang) || voices.find(v => v.lang.startsWith("en"));
  if (preferred) u.voice = preferred;
  window.speechSynthesis.speak(u);
}

/* ---------- Keyboard shortcuts ---------- */
document.addEventListener("keydown", (e) => {
  // Ignore while typing in inputs
  if (e.target.matches("input,textarea,select,[contenteditable]")) return;
  if (e.key === "/" ) { /* '/' handled below */ }
  // 'F' or 'f' to flip flashcards (when results visible)
  if (e.key === "f" || e.key === "F") {
    const fc = document.querySelector(".flashcard:not(.flipped)");
    if (fc) { fc.classList.add("flipped"); e.preventDefault(); return; }
    const fc2 = document.querySelector(".flashcard.flipped");
    if (fc2) { fc2.classList.remove("flipped"); e.preventDefault(); return; }
  }
  // 'T' opens tutor
  if (e.key === "t" || e.key === "T") {
    const fab = document.getElementById("tutor-fab");
    if (fab && fab.style.display !== "none") { fab.click(); e.preventDefault(); }
  }
  // '?' shows shortcut help
  if (e.key === "?") {
    toast("⌨️ Shortcuts: F = flip flashcard · T = AI Tutor · 1-4 = answer MCQ · Esc = close tutor");
    e.preventDefault();
  }
});
// MCQ keyboard: 1/2/3/4 or A/B/C/D to pick options in the first unanswered MCQ
document.addEventListener("keydown", (e) => {
  if (e.target.matches("input,textarea,select,[contenteditable]")) return;
  const key = e.key.toUpperCase();
  const map = {"1":"A","2":"B","3":"C","4":"D","A":"A","B":"B","C":"C","D":"D"};
  if (!map[key]) return;
  const mcq = document.querySelector(".mcq:not(.explained)");
  if (!mcq) return;
  const opt = mcq.querySelector(`.mcq-option[data-label="${map[key]}"]`);
  if (opt) { opt.click(); e.preventDefault(); }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeTutor();
});

/* ===============================================================
   Exam Mitra v2.4 — Photo Syllabus Upload + PWA
   =============================================================== */

/* ---------- Photo Syllabus Upload (multimodal vision OCR) ---------- */
(() => {
  const photoInput = document.getElementById("photo-input");
  const photoStatus = document.getElementById("photo-status");
  const syllabusTA = document.getElementById("syllabus");
  const photoBtnLabel = document.getElementById("photo-btn-label");
  if (!photoInput) return;

  function setStatus(type, html) {
    if (!photoStatus) return;
    photoStatus.className = `photo-status ${type}`;
    photoStatus.innerHTML = html;
    photoStatus.style.display = type ? "block" : "none";
  }

  photoInput.addEventListener("change", async () => {
    const file = photoInput.files && photoInput.files[0];
    if (!file) return;

    // Quick client-side size check
    if (file.size > 8 * 1024 * 1024) {
      setStatus("error", "⚠️ File too large. Please use an image under 8 MB.");
      return;
    }

    setStatus("loading", `<span class="spinner"></span>Reading photo with AI vision… this takes 4-8 seconds. Tip: make sure chapter/topic names are in focus.`);
    photoBtnLabel.textContent = "⏳ Scanning…";

    const examVal = (document.getElementById("exam") || {}).value || "";
    const langVal = (document.getElementById("language") || {}).value || "en";

    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("exam", examVal);
      fd.append("language", langVal);

      const resp = await fetch("/api/extract-syllabus", {
        method: "POST",
        body: fd,
      });

      if (!resp.ok) {
        let err = `Upload failed (${resp.status})`;
        try { const j = await resp.json(); err = j.detail || j.error || err; } catch(_) {}
        throw new Error(err);
      }

      const data = await resp.json();
      const extracted = data.extracted_text || "";

      if (extracted.startsWith("[UNRECOGNIZED]")) {
        setStatus("error", "⚠️ Could not recognize a syllabus in this image. Try a clearer photo of your syllabus/TOC, or type the topics manually.<br><small>" + extracted.slice(15).slice(0,200) + "</small>");
      } else {
        // Insert into syllabus textarea (append or replace if empty)
        const current = syllabusTA.value.trim();
        const joiner = current ? "\n\n[Extracted from photo]:\n" : "";
        syllabusTA.value = current + joiner + extracted;
        setStatus("success", `✅ Syllabus extracted (${extracted.length} chars). Review, edit if needed, then click Generate. <a href="#" id="reupload-link" style="color:#065f46;text-decoration:underline;font-weight:600">Upload another?</a>`);
        document.getElementById("reupload-link")?.addEventListener("click", (e) => {
          e.preventDefault();
          photoInput.value = "";
          setStatus("", "");
          photoBtnLabel.textContent = "Upload photo of syllabus";
        });
        toast("📸 Syllabus extracted — review and edit if needed!");
      }
    } catch (err) {
      setStatus("error", `⚠️ ${esc(err.message || "Upload failed")}. You can still paste the syllabus manually.`);
    } finally {
      photoBtnLabel.textContent = "Upload photo of syllabus";
    }
  });
})();

/* ---------- PWA: Service Worker registration + Install banner ---------- */
(() => {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/static/sw.js").catch((err) => {
        console.warn("SW registration failed:", err);
      });
    });
  }

  // PWA install prompt
  let deferredPrompt = null;
  const dismissed = localStorage.getItem("em_pwa_dismissed");

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (dismissed && Date.now() - Number(dismissed) < 7 * 24 * 60 * 60 * 1000) return; // don't show within 7 days of dismiss
    setTimeout(showInstallBanner, 4000); // wait a few seconds after page load
  });

  function showInstallBanner() {
    // Don't show if already running in standalone/installed mode
    if (window.matchMedia("(display-mode: standalone)").matches) return;
    let banner = document.getElementById("pwa-install-banner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "pwa-install-banner";
      banner.className = "pwa-install-banner";
      banner.innerHTML = `
        <span>📱 Install Exam Mitra on your phone — works offline!</span>
        <button class="install-btn">Install</button>
        <button class="dismiss" aria-label="Dismiss">✕</button>
      `;
      document.body.appendChild(banner);
      banner.querySelector(".install-btn").addEventListener("click", async () => {
        if (deferredPrompt) {
          deferredPrompt.prompt();
          await deferredPrompt.userChoice;
          deferredPrompt = null;
        }
        banner.classList.remove("show");
      });
      banner.querySelector(".dismiss").addEventListener("click", () => {
        banner.classList.remove("show");
        localStorage.setItem("em_pwa_dismissed", String(Date.now()));
      });
    }
    banner.classList.add("show");
  }
})();

/* ---- On load: auto-load ?job=XXX ---- */
window.addEventListener("DOMContentLoaded", () => {
  ensureTutorDOMElements();
  // Ensure voices are loaded (Chrome lazy-loads them)
  if ("speechSynthesis" in window) { window.speechSynthesis.getVoices(); window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices(); }
  const params = new URLSearchParams(location.search);
  const existingJob = params.get("job");
  if (existingJob) {
    (async () => {
      try {
        const r = await fetch(`/api/jobs/${existingJob}`);
        if (!r.ok) return;
        const j = await r.json();
        if (j.status === "complete") {
          renderResults(existingJob, j);
        } else if (j.status === "error") {
          showError(j.error || "Plan not available.");
        } else {
          progressSection.classList.remove("hidden");
          renderProgress(j.step || 1, j);
          await connectSSE(existingJob);
        }
      } catch(e) {
        console.log("No existing job to resume:", e);
      }
    })();
  }
});
