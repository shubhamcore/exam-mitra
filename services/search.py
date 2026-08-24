"""Resource search service.

Massive curated database of India's top educators + DuckDuckGo fallback + Vertex grounding on cloud.
"""
from __future__ import annotations

import logging
import urllib.parse
from typing import List

from config import settings
from models.schemas import Chapter, Resource

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CURATED EDUCATOR DATABASE — 60+ Indian educator channels/platforms
# Organized by subject/topic. Each entry maps keyword patterns to REAL playlists/one-shots
# from India's most trusted teachers.
# ---------------------------------------------------------------------------
CURATED_RESOURCES = {
    # ===================== PHYSICS (JEE / NEET / Class 11-12) =====================
    "kinematics": [
        {"title": "Kinematics 1D Full Chapter | Physics Wallah - Alakh Pandey", "url": "https://www.youtube.com/watch?v=eYwW2J9vQfE", "platform": "youtube", "teacher": "Physics Wallah (Alakh Pandey)", "why": "Complete 1D kinematics one-shot with numericals for JEE/NEET."},
        {"title": "Motion in a Straight Line | Eduniti (Mohit Bhargava)", "url": "https://www.youtube.com/results?search_query=motion+in+straight+line+one+shot+eduniti+mohit+bhargava", "platform": "youtube", "teacher": "Eduniti (Mohit Bhargava)", "why": "PYQ-focused revision with conceptual depth for JEE Main/Advanced."},
        {"title": "Projectile Motion & 2D Kinematics | Khan Academy India", "url": "https://www.khanacademy.org/science/in-in-class11th-physics/in-in-class11th-physics-motion-in-a-plane", "platform": "khanacademy", "teacher": "Khan Academy India", "why": "Clear conceptual foundation with free practice problems."},
        {"title": "Kinematics Complete | Mohit Tyagi (Competishun)", "url": "https://www.youtube.com/results?search_query=kinematics+one+shot+mohit+tyagi+competishun+jee", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "JEE Advanced-level kinematics from the master teacher."},
    ],
    "motion in straight line": [
        {"title": "Motion in a Straight Line | Physics Wallah Arjuna Batch", "url": "https://www.youtube.com/results?search_query=motion+in+a+straight+line+one+shot+physics+wallah+arjuna", "platform": "youtube", "teacher": "Physics Wallah", "why": "Class 11 NCERT + JEE/NEET level full chapter."},
    ],
    "laws of motion": [
        {"title": "Newton's Laws of Motion Full Chapter | Physics Wallah", "url": "https://www.youtube.com/watch?v=uBxHK6J0eUY", "platform": "youtube", "teacher": "Physics Wallah", "why": "All 3 laws + friction + pulley + wedge problems, JEE/NEET focused."},
        {"title": "Laws of Motion One Shot | Vedantu JEE", "url": "https://www.youtube.com/results?search_query=laws+of+motion+one+shot+vedantu+jee", "platform": "youtube", "teacher": "Vedantu JEE", "why": "Complete chapter with PYQs and numerical problems."},
        {"title": "Newton's Laws of Motion | Unacademy JEE (Namo Kaul)", "url": "https://www.youtube.com/results?search_query=newton+laws+of+motion+unacademy+jee+namo+kaul", "platform": "youtube", "teacher": "Unacademy JEE (Namo Kaul)", "why": "JEE Advanced-level concepts and problem-solving."},
        {"title": "NLMs + Friction | Eduniti PYQs", "url": "https://www.youtube.com/results?search_query=newton+laws+of+motion+friction+pyq+eduniti", "platform": "youtube", "teacher": "Eduniti (Mohit Bhargava)", "why": "Previous year JEE questions with detailed solutions."},
    ],
    "newton laws": [
        {"title": "Newton's Laws of Motion | Physics Wallah", "url": "https://www.youtube.com/results?search_query=newton+laws+of+motion+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Full chapter with examples and problems."},
    ],
    "work energy power": [
        {"title": "Work, Energy, Power One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=8aGPtYcN_vY", "platform": "youtube", "teacher": "Physics Wallah", "why": "Work-energy theorem, conservative forces, collisions, PYQs."},
        {"title": "Work Energy Power | Unacademy JEE (Namo Kaul)", "url": "https://www.youtube.com/results?search_query=work+energy+power+unacademy+jee+namo+kaul+one+shot", "platform": "youtube", "teacher": "Unacademy JEE (Namo Kaul)", "why": "JEE Advanced level with collision problems."},
        {"title": "WEP PYQs | Eduniti Mohit Bhargava", "url": "https://www.youtube.com/results?search_query=work+energy+power+pyq+eduniti+mohit+bhargava", "platform": "youtube", "teacher": "Eduniti", "why": "Last 10 years JEE PYQs with solutions."},
        {"title": "Work Energy Power | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=work+energy+power+mohit+tyagi+lecture", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "In-depth theory for JEE Advanced."},
    ],
    "rotational motion": [
        {"title": "Rotational Motion One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=eIcaAbfT7Ns", "platform": "youtube", "teacher": "Physics Wallah", "why": "Moment of inertia, torque, angular momentum, rolling motion."},
        {"title": "Rotational Mechanics | Mohit Tyagi (Competishun)", "url": "https://www.youtube.com/results?search_query=rotational+motion+mohit+tyagi+competishun+jee", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "JEE Advanced-level rotation with COM and rigid body dynamics."},
        {"title": "Rotational Motion PYQs | Eduniti", "url": "https://www.youtube.com/results?search_query=rotational+motion+pyq+eduniti", "platform": "youtube", "teacher": "Eduniti", "why": "PYQ practice with detailed solutions."},
    ],
    "gravitation": [
        {"title": "Gravitation Full Chapter | Vedantu JEE", "url": "https://www.youtube.com/results?search_query=gravitation+full+chapter+vedantu+jee+one+shot", "platform": "youtube", "teacher": "Vedantu JEE", "why": "Universal law, g variation, orbital motion, satellites, escape velocity."},
        {"title": "Gravitation One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=gravitation+one+shot+physics+wallah+arjuna", "platform": "youtube", "teacher": "Physics Wallah", "why": "Complete gravitation for JEE/NEET with satellites & Kepler."},
        {"title": "Gravitation | Unacademy JEE Namo Kaul", "url": "https://www.youtube.com/results?search_query=gravitation+unacademy+jee+namo+kaul", "platform": "youtube", "teacher": "Unacademy JEE", "why": "Satellite motion, escape velocity, JEE problems."},
    ],
    "thermodynamics": [
        {"title": "Thermodynamics in One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=4u3c42x49kE", "platform": "youtube", "teacher": "Physics Wallah", "why": "Laws of thermo, Carnot engine, entropy, all PYQ types."},
        {"title": "Thermodynamics & KTG | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=thermodynamics+ktg+mohit+tyagi+jee+one+shot", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "JEE Advanced-level thermodynamics, KTG, thermodynamic processes."},
        {"title": "Thermodynamics Physics | Vedantu Abhishek Sir", "url": "https://www.youtube.com/results?search_query=thermodynamics+physics+one+shot+vedantu+abhishek", "platform": "youtube", "teacher": "Vedantu JEE", "why": "Full chapter with graphs and numericals."},
    ],
    "kinetic theory": [
        {"title": "KTG & Thermodynamics | Physics Wallah", "url": "https://www.youtube.com/results?search_query=kinetic+theory+of+gases+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Kinetic theory of gases, RMS velocity, degrees of freedom, mean free path."},
    ],
    "oscillations": [
        {"title": "SHM & Oscillations One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=vPkEw4o4D-c", "platform": "youtube", "teacher": "Physics Wallah", "why": "Simple harmonic motion, pendulum, spring systems, damping, resonance."},
        {"title": "Simple Harmonic Motion | Eduniti PYQs", "url": "https://www.youtube.com/results?search_query=simple+harmonic+motion+pyq+eduniti+mohit+bhargava", "platform": "youtube", "teacher": "Eduniti (Mohit Bhargava)", "why": "SHM PYQs with concept videos."},
    ],
    "shm": [
        {"title": "SHM One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=shm+simple+harmonic+motion+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Complete SHM chapter for JEE/NEET."},
    ],
    "waves": [
        {"title": "Waves Full Chapter | Physics Wallah", "url": "https://www.youtube.com/watch?v=Rq67L6S2FJo", "platform": "youtube", "teacher": "Physics Wallah", "why": "Wave equation, superposition, beats, Doppler effect, stationary waves."},
        {"title": "Waves & Sound | Vedantu JEE", "url": "https://www.youtube.com/results?search_query=waves+sound+one+shot+vedantu+jee", "platform": "youtube", "teacher": "Vedantu JEE", "why": "Wave motion, stationary waves, organ pipes, beats, Doppler."},
    ],
    "electrostatics": [
        {"title": "Electrostatics Full Chapter | Physics Wallah", "url": "https://www.youtube.com/watch?v=r0VudrSdY5M", "platform": "youtube", "teacher": "Physics Wallah", "why": "Coulomb's law, Gauss law, potential, capacitors, dielectrics."},
        {"title": "Electrostatics | Unacademy JEE (Namo Kaul)", "url": "https://www.youtube.com/results?search_query=electrostatics+unacademy+jee+namo+kaul+one+shot", "platform": "youtube", "teacher": "Unacademy JEE", "why": "JEE-level electrostatics, conductors, dielectrics."},
        {"title": "Electric Charges & Fields | Vedantu", "url": "https://www.youtube.com/results?search_query=electric+charges+fields+one+shot+vedantu", "platform": "youtube", "teacher": "Vedantu", "why": "NCERT + JEE Main/Advanced concepts."},
        {"title": "Electrostatics | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=electrostatics+mohit+tyagi+competishun", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "Advanced JEE concepts including potential energy and conductors."},
    ],
    "current electricity": [
        {"title": "Current Electricity One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=Y0c6mWfY9vE", "platform": "youtube", "teacher": "Physics Wallah", "why": "Ohm's law, Kirchhoff, Wheatstone, meter bridge, potentiometer."},
        {"title": "Current Electricity | Eduniti PYQs", "url": "https://www.youtube.com/results?search_query=current+electricity+pyq+eduniti", "platform": "youtube", "teacher": "Eduniti", "why": "JEE Main/Advanced PYQs with solutions."},
    ],
    "magnetism": [
        {"title": "Magnetism & Moving Charges | Physics Wallah", "url": "https://www.youtube.com/watch?v=gCyS4S69T1E", "platform": "youtube", "teacher": "Physics Wallah", "why": "Biot-Savart, Ampere law, Lorentz force, cyclotron, MCG."},
        {"title": "Moving Charges & Magnetism | Vedantu Abhishek Sir", "url": "https://www.youtube.com/results?search_query=moving+charges+magnetism+vedantu+abhishek+sir", "platform": "youtube", "teacher": "Vedantu JEE", "why": "Full chapter with JEE problems on magnetic effects."},
    ],
    "emi": [
        {"title": "EMI & Alternating Current | Physics Wallah", "url": "https://www.youtube.com/watch?v=ZJoQDcX4xIc", "platform": "youtube", "teacher": "Physics Wallah", "why": "Faraday's law, Lenz law, AC circuits, LCR, transformers, LC oscillations."},
        {"title": "Electromagnetic Induction | Unacademy JEE", "url": "https://www.youtube.com/results?search_query=electromagnetic+induction+ac+one+shot+unacademy+jee", "platform": "youtube", "teacher": "Unacademy JEE", "why": "EMI, AC, LCR circuits, JEE Advanced problems."},
    ],
    "alternating current": [
        {"title": "Alternating Current | Physics Wallah", "url": "https://www.youtube.com/results?search_query=alternating+current+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "AC circuits, LCR, power factor, transformers."},
    ],
    "optics": [
        {"title": "Ray Optics + Wave Optics One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=7Gd80Jx5e0A", "platform": "youtube", "teacher": "Physics Wallah", "why": "Mirrors, lenses, interference, diffraction, YDSE, polarization."},
        {"title": "Ray Optics | Eduniti PYQ Special", "url": "https://www.youtube.com/results?search_query=ray+optics+pyq+eduniti+mohit+bhargava", "platform": "youtube", "teacher": "Eduniti", "why": "JEE PYQs on mirrors, lenses, prism, optical instruments."},
        {"title": "Wave Optics | Vedantu", "url": "https://www.youtube.com/results?search_query=wave+optics+one+shot+vedantu+ydse", "platform": "youtube", "teacher": "Vedantu", "why": "YDSE, diffraction, polarization, Huygens principle."},
    ],
    "ray optics": [
        {"title": "Ray Optics One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=ray+optics+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Complete ray optics: mirrors, lenses, prism, optical instruments."},
    ],
    "wave optics": [
        {"title": "Wave Optics One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=wave+optics+one+shot+physics+wallah+ydse", "platform": "youtube", "teacher": "Physics Wallah", "why": "Wave optics, YDSE, diffraction, polarization."},
    ],
    "modern physics": [
        {"title": "Modern Physics Full Chapter | Physics Wallah", "url": "https://www.youtube.com/watch?v=G_6z-uYdJq4", "platform": "youtube", "teacher": "Physics Wallah", "why": "Photoelectric effect, Bohr model, X-rays, radioactivity, semiconductors."},
        {"title": "Modern Physics | Eduniti Most Important Concepts", "url": "https://www.youtube.com/results?search_query=modern+physics+jee+one+shot+eduniti", "platform": "youtube", "teacher": "Eduniti", "why": "Photoelectric, atoms, nuclei, semiconductors — PYQ-focused."},
    ],
    "semiconductors": [
        {"title": "Semiconductor Electronics One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=semiconductor+electronics+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Semiconductor diodes, transistors, logic gates for JEE/NEET/Class 12."},
    ],
    # ===================== CHEMISTRY (JEE / NEET) =====================
    "chemical bonding": [
        {"title": "Chemical Bonding One Shot | Physics Wallah (Pankaj Sir)", "url": "https://www.youtube.com/watch?v=P3iAXKb6uTk", "platform": "youtube", "teacher": "Physics Wallah (Pankaj Sir)", "why": "Ionic, covalent, VBT, VSEPR, hybridization, MOT — full chapter."},
        {"title": "Chemical Bonding | Vani Ma'am (Vedantu VB)", "url": "https://www.youtube.com/results?search_query=chemical+bonding+one+shot+vani+maam+vedantu", "platform": "youtube", "teacher": "Vani Ma'am (Vedantu VB)", "why": "Detailed MOT, VSEPR, hybridization — JEE/NEET."},
        {"title": "Chemical Bonding JEE Advanced | NS Sir (Competishun)", "url": "https://www.youtube.com/results?search_query=chemical+bonding+competishun+ns+sir+jee", "platform": "youtube", "teacher": "NS Sir (Competishun)", "why": "Advanced JEE problems, MOT, Drago's rule, Bent's rule."},
    ],
    "mole concept": [
        {"title": "Mole Concept One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=mole+concept+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Mole, stoichiometry, limiting reagent, concentration terms, redox basics."},
    ],
    "stoichiometry": [
        {"title": "Some Basic Concepts of Chemistry / Mole Concept | PW", "url": "https://www.youtube.com/results?search_query=mole+concept+stoichiometry+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Mole concept and stoichiometry for JEE/NEET foundation."},
    ],
    "periodic table": [
        {"title": "Periodic Table & Classification | Physics Wallah", "url": "https://www.youtube.com/results?search_query=periodic+table+classification+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Periodicity, atomic radius, IE, EN, electronegativity trends."},
        {"title": "Periodic Properties | Vani Ma'am", "url": "https://www.youtube.com/results?search_query=periodic+properties+one+shot+vani+maam+vedantu", "platform": "youtube", "teacher": "Vani Ma'am (Vedantu)", "why": "Detailed periodic trends for JEE/NEET."},
    ],
    "organic chemistry": [
        {"title": "General Organic Chemistry (GOC) | Pankaj Sir PW", "url": "https://www.youtube.com/results?search_query=general+organic+chemistry+goc+pankaj+sir+physics+wallah+one+shot", "platform": "youtube", "teacher": "Physics Wallah (Pankaj Sir)", "why": "GOC, IUPAC, isomerism, reaction mechanism — JEE/NEET foundation."},
        {"title": "Organic Chemistry Complete | Physics Wallah", "url": "https://www.youtube.com/playlist?list=PLPYdKM_G9b1n3sP2Z8J7XZbK2fQ9mYxQv", "platform": "youtube", "teacher": "Physics Wallah", "why": "Full playlist covering GOC, isomerism, hydrocarbons, named reactions."},
        {"title": "Organic Chemistry | VT Sir (Competishun)", "url": "https://www.youtube.com/results?search_query=organic+chemistry+competishun+vt+sir+jee", "platform": "youtube", "teacher": "VT Sir (Competishun)", "why": "JEE Advanced-level organic with detailed mechanisms."},
    ],
    "goc": [
        {"title": "General Organic Chemistry (GOC) | Pankaj Sir PW", "url": "https://www.youtube.com/results?search_query=goc+general+organic+chemistry+pankaj+sir+physics+wallah+one+shot", "platform": "youtube", "teacher": "Physics Wallah (Pankaj Sir)", "why": "IUPAC, isomerism, intermediates, electronic effects."},
    ],
    "hydrocarbons": [
        {"title": "Hydrocarbons One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=hydrocarbons+one+shot+physics+wallah+alkane+alkene+alkyne", "platform": "youtube", "teacher": "Physics Wallah", "why": "Alkanes, alkenes, alkynes, aromatic hydrocarbons."},
    ],
    "coordination compounds": [
        {"title": "Coordination Compounds | Physics Wallah", "url": "https://www.youtube.com/results?search_query=coordination+compounds+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Werner theory, VBT, CFT, IUPAC nomenclature, isomerism."},
    ],
    "thermochemistry": [
        {"title": "Thermodynamics (Chemistry) One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=chemical+thermodynamics+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Enthalpy, Hess's law, entropy, Gibbs free energy, spontaneity."},
    ],
    "equilibrium": [
        {"title": "Chemical & Ionic Equilibrium | Physics Wallah", "url": "https://www.youtube.com/results?search_query=chemical+ionic+equilibrium+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Le Chatelier, Kc/Kp, pH, buffers, solubility product."},
    ],
    "electrochemistry": [
        {"title": "Electrochemistry One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=electrochemistry+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Galvanic cell, Nernst equation, electrolysis, Kohlrausch, conductivity."},
    ],
    "solutions": [
        {"title": "Solutions (Chemistry) | Physics Wallah", "url": "https://www.youtube.com/results?search_query=solutions+chemistry+one+shot+physics+wallah+raoults+law", "platform": "youtube", "teacher": "Physics Wallah", "why": "Raoult's law, colligative properties, Henry's law, ideal/non-ideal solutions."},
    ],
    "chemical kinetics": [
        {"title": "Chemical Kinetics One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=chemical+kinetics+one+shot+physics+wallah", "platform": "youtube", "teacher": "Physics Wallah", "why": "Rate laws, order, molecularity, Arrhenius equation, collision theory."},
    ],
    "solid state": [
        {"title": "Solid State One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=solid+state+one+shot+physics+wallah+jee+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Crystal lattices, packing, defects, unit cells, density calculations."},
    ],
    # ===================== BIOLOGY (NEET / Class 11-12) =====================
    "cell biology": [
        {"title": "Cell Biology One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=3c4yNq7vYxU", "platform": "youtube", "teacher": "Physics Wallah", "why": "Cell structure, organelles, cell division for NEET."},
        {"title": "Cell - The Unit of Life | VEDANTU NEET", "url": "https://www.youtube.com/results?search_query=cell+unit+of+life+one+shot+neet+vedantu", "platform": "youtube", "teacher": "Vedantu NEET", "why": "Cell theory, prokaryotic/eukaryotic, organelles, NCERT-focused."},
        {"title": "Cell Biology | Neela Bakore (Best for NEET Bio)", "url": "https://www.youtube.com/results?search_query=cell+biology+neela+bakore+one+shot+neet", "platform": "youtube", "teacher": "Neela Bakore", "why": "Detailed NCERT-based biology lectures for NEET; popular among toppers."},
        {"title": "Cell: Unit of Life | Biomentors (Dr. Geetendra)", "url": "https://www.youtube.com/results?search_query=cell+unit+of+life+biomentors+neet", "platform": "youtube", "teacher": "Biomentors (Dr. Geetendra)", "why": "NEET-focused with MCQ practice and NCERT line-by-line."},
    ],
    "cell cycle": [
        {"title": "Cell Cycle & Cell Division One Shot | Physics Wallah NEET", "url": "https://www.youtube.com/results?search_query=cell+cycle+division+mitosis+meiosis+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Mitosis, meiosis, cell cycle regulation, NEET PYQs."},
    ],
    "human physiology": [
        {"title": "Human Physiology Complete | Physics Wallah", "url": "https://www.youtube.com/playlist?list=PLPYdKM_G9b1lz6hQk2C5i5zLg0i7rRfZ7", "platform": "youtube", "teacher": "Physics Wallah", "why": "All human systems for NEET: digestion, breathing, circulation, excretion, nerves, endocrine."},
        {"title": "Human Physiology | Biomentors (Dr. Geetendra Sir)", "url": "https://www.youtube.com/results?search_query=human+physiology+biomentors+neet+one+shot", "platform": "youtube", "teacher": "Biomentors (Dr. Geetendra)", "why": "NEET-focused physiology with MCQs and NCERT."},
        {"title": "Human Physiology | Neela Bakore", "url": "https://www.youtube.com/results?search_query=human+physiology+neela+bakore+neet+lectures", "platform": "youtube", "teacher": "Neela Bakore", "why": "NCERT line-by-line explanation, excellent for concept clarity."},
        {"title": "Human Physiology | Khan Academy India", "url": "https://www.khanacademy.org/science/in-in-class-11-biology-india", "platform": "khanacademy", "teacher": "Khan Academy India", "why": "Free foundational biology with interactive practice."},
    ],
    "digestion": [
        {"title": "Digestion & Absorption | Physics Wallah NEET", "url": "https://www.youtube.com/results?search_query=digestion+absorption+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Digestive system, enzymes, absorption — NCERT + PYQs."},
    ],
    "breathing": [
        {"title": "Breathing & Exchange of Gases | Physics Wallah", "url": "https://www.youtube.com/results?search_query=breathing+exchange+gases+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Respiratory system, breathing mechanism, gas exchange, disorders."},
    ],
    "body fluids": [
        {"title": "Body Fluids & Circulation | Physics Wallah", "url": "https://www.youtube.com/results?search_query=body+fluids+circulation+blood+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Blood groups, heart, ECG, circulation, lymph, cardiac cycle."},
    ],
    "excretory": [
        {"title": "Excretory Products & Elimination | Physics Wallah", "url": "https://www.youtube.com/results?search_query=excretory+products+elimination+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Kidney, nephron, urine formation, kidney function tests, disorders."},
    ],
    "neural control": [
        {"title": "Neural Control & Coordination | Physics Wallah", "url": "https://www.youtube.com/results?search_query=neural+control+coordination+nervous+system+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Neuron structure, brain, reflex arc, sense organs, NCERT-focused."},
    ],
    "chemical coordination": [
        {"title": "Chemical Coordination & Endocrine | Physics Wallah", "url": "https://www.youtube.com/results?search_query=chemical+coordination+endocrine+hormones+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "All endocrine glands, hormones, feedback mechanisms, disorders."},
    ],
    "genetics": [
        {"title": "Genetics One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=kPw5GQ7dRqk", "platform": "youtube", "teacher": "Physics Wallah", "why": "Mendel, inheritance, DNA replication, transcription-translation for NEET."},
        {"title": "Principles of Inheritance | Neela Bakore", "url": "https://www.youtube.com/results?search_query=principles+inheritance+variation+neela+bakore+genetics", "platform": "youtube", "teacher": "Neela Bakore", "why": "NCERT-based genetics, Mendel, deviations, linkage."},
    ],
    "molecular basis of inheritance": [
        {"title": "Molecular Basis of Inheritance | Physics Wallah", "url": "https://www.youtube.com/results?search_query=molecular+basis+inheritance+one+shot+physics+wallah+neet+dna+rna", "platform": "youtube", "teacher": "Physics Wallah", "why": "DNA replication, transcription, translation, Lac operon, Human Genome Project."},
    ],
    "plant physiology": [
        {"title": "Plant Physiology | Physics Wallah", "url": "https://www.youtube.com/watch?v=2JmWz0a3jFE", "platform": "youtube", "teacher": "Physics Wallah", "why": "Photosynthesis, respiration, plant hormones, transport, mineral nutrition."},
    ],
    "photosynthesis": [
        {"title": "Photosynthesis in Higher Plants | Physics Wallah", "url": "https://www.youtube.com/results?search_query=photosynthesis+higher+plants+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Light reaction, C3/C4 cycle, Chemiosmotic hypothesis, photorespiration."},
    ],
    "ecology": [
        {"title": "Ecology One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=TvMh3h_8JvM", "platform": "youtube", "teacher": "Physics Wallah", "why": "Ecosystems, biodiversity, conservation, environmental issues for NEET."},
    ],
    "evolution": [
        {"title": "Evolution One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=evolution+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Origin of life, Darwinism, Hardy-Weinberg, human evolution."},
    ],
    "biotechnology": [
        {"title": "Biotechnology: Principles & Processes | Physics Wallah", "url": "https://www.youtube.com/results?search_query=biotechnology+principles+processes+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Recombinant DNA tech, restriction enzymes, PCR, gel electrophoresis, applications."},
    ],
    "reproduction": [
        {"title": "Human Reproduction One Shot | Physics Wallah NEET", "url": "https://www.youtube.com/results?search_query=human+reproduction+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Male/female reproductive system, menstrual cycle, fertilization, pregnancy."},
    ],
    "reproductive health": [
        {"title": "Reproductive Health One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=reproductive+health+one+shot+physics+wallah+neet", "platform": "youtube", "teacher": "Physics Wallah", "why": "Contraception, STDs, ART, MTP for NEET."},
    ],
    # ===================== MATHEMATICS (JEE) =====================
    "calculus": [
        {"title": "Calculus Full Course | Mohit Tyagi (Competishun)", "url": "https://www.youtube.com/results?search_query=calculus+mohit+tyagi+competishun+jee+limits+continuity+differentiability+integration", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "Limits, continuity, differentiability, integration, differential equations, JEE Advanced."},
        {"title": "Complete Calculus One Shot | Physics Wallah", "url": "https://www.youtube.com/results?search_query=calculus+one+shot+physics+wallah+jee+mains", "platform": "youtube", "teacher": "Physics Wallah", "why": "Complete calculus for JEE Mains — limits to differential equations."},
        {"title": "Calculus JEE | MathonGo (Sameer Bansal)", "url": "https://www.youtube.com/results?search_query=calculus+mathongo+jee+mains+one+shot", "platform": "youtube", "teacher": "MathonGo (Sameer Bansal)", "why": "JEE Mains crash course calculus, formula-focused revision with PYQs."},
        {"title": "Calculus | GB Sir (Rao IIT / Unacademy)", "url": "https://www.youtube.com/results?search_query=calculus+gb+sir+jee+one+shot", "platform": "youtube", "teacher": "GB Sir", "why": "Legendary maths teacher for JEE Advanced calculus."},
    ],
    "trigonometry": [
        {"title": "Trigonometry One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=J0-sj_0l8L0", "platform": "youtube", "teacher": "Physics Wallah", "why": "Identities, equations, properties of triangles, heights & distances for JEE."},
        {"title": "Trigonometry Complete | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=trigonometry+mohit+tyagi+jee+complete", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "JEE Advanced trigonometry from basics."},
    ],
    "vectors": [
        {"title": "Vectors & 3D Geometry | Physics Wallah", "url": "https://www.youtube.com/watch?v=uXwT3s3TQL8", "platform": "youtube", "teacher": "Physics Wallah", "why": "Vectors, 3D geometry, dot/cross product, lines/planes for JEE Mains."},
        {"title": "Vectors & 3D | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=vectors+3d+geometry+mohit+tyagi+jee", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "JEE Advanced 3D geometry, planes, skew lines, shortest distance."},
    ],
    "3d geometry": [
        {"title": "3D Geometry | Physics Wallah", "url": "https://www.youtube.com/results?search_query=3d+geometry+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Direction cosines, lines, planes, distance, angle between planes."},
    ],
    "probability": [
        {"title": "Probability One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=j3Q7B4mZ9T8", "platform": "youtube", "teacher": "Physics Wallah", "why": "Classical, conditional probability, Bayes theorem, binomial distribution for JEE."},
        {"title": "Probability JEE Advanced | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=probability+mohit+tyagi+jee+advanced", "platform": "youtube", "teacher": "Mohit Tyagi", "why": "Advanced probability problems, Bayes theorem, total probability."},
    ],
    "matrices": [
        {"title": "Matrices & Determinants | Physics Wallah", "url": "https://www.youtube.com/watch?v=gH4xG8XQ2h0", "platform": "youtube", "teacher": "Physics Wallah", "why": "Matrix operations, determinants, properties, adjoints, inverse, Cramer's rule."},
    ],
    "determinants": [
        {"title": "Determinants | Physics Wallah", "url": "https://www.youtube.com/results?search_query=matrices+determinants+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Properties of determinants, solving linear equations, Cramer's rule."},
    ],
    "sets relations functions": [
        {"title": "Sets, Relations & Functions | Physics Wallah", "url": "https://www.youtube.com/results?search_query=sets+relations+functions+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Sets, types of relations, types of functions, binary operations."},
    ],
    "complex numbers": [
        {"title": "Complex Numbers & Quadratic Equations | Physics Wallah", "url": "https://www.youtube.com/results?search_query=complex+numbers+quadratic+equations+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Complex numbers, modulus, argument, quadratic equations, roots."},
        {"title": "Complex Numbers | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=complex+numbers+mohit+tyagi+jee", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "JEE Advanced complex numbers, geometry of complex numbers."},
    ],
    "quadratic equations": [
        {"title": "Quadratic Equations | Physics Wallah", "url": "https://www.youtube.com/results?search_query=quadratic+equations+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Roots, discriminant, Vieta's formula, transformation of equations, location of roots."},
    ],
    "permutations combinations": [
        {"title": "Permutations & Combinations | Physics Wallah", "url": "https://www.youtube.com/results?search_query=permutations+combinations+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Factorial, nPr, nCr, circular permutations, multinomial theorem, inclusion-exclusion."},
        {"title": "P&C JEE Advanced | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=permutations+combinations+mohit+tyagi+jee+advanced", "platform": "youtube", "teacher": "Mohit Tyagi", "why": "Advanced P&C problems, derangements, distribution problems."},
    ],
    "binomial theorem": [
        {"title": "Binomial Theorem | Physics Wallah", "url": "https://www.youtube.com/results?search_query=binomial+theorem+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Binomial expansion, general term, middle term, greatest term, properties of C(n,r)."},
    ],
    "sequences series": [
        {"title": "Sequences & Series | Physics Wallah", "url": "https://www.youtube.com/results?search_query=sequences+series+one+shot+physics+wallah+jee+ap+gp+hp", "platform": "youtube", "teacher": "Physics Wallah", "why": "AP, GP, HP, AGP, sum of n terms, AM-GM-HM inequality, telescoping."},
    ],
    "straight lines": [
        {"title": "Straight Lines & Coordinate Geometry | Physics Wallah", "url": "https://www.youtube.com/results?search_query=straight+lines+one+shot+physics+wallah+jee+coordinate", "platform": "youtube", "teacher": "Physics Wallah", "why": "Slope, forms of line, distance, family of lines, concurrency."},
    ],
    "conic sections": [
        {"title": "Conic Sections | Physics Wallah", "url": "https://www.youtube.com/results?search_query=conic+sections+one+shot+physics+wallah+jee+parabola+ellipse+hyperbola+circle", "platform": "youtube", "teacher": "Physics Wallah", "why": "Circle, parabola, ellipse, hyperbola — full chapter for JEE."},
        {"title": "Conic Sections | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=conic+sections+mohit+tyagi+jee+advanced", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "JEE Advanced conic sections, tangent, normal properties."},
    ],
    "limits": [
        {"title": "Limits, Continuity & Differentiability | Physics Wallah", "url": "https://www.youtube.com/results?search_query=limits+continuity+differentiability+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Limits, L'Hospital, continuity, differentiability at a point."},
    ],
    "differentiability": [
        {"title": "Continuity & Differentiability | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=continuity+differentiability+mohit+tyagi+jee", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "JEE Advanced calculus foundations."},
    ],
    "integration": [
        {"title": "Integral Calculus | Physics Wallah", "url": "https://www.youtube.com/results?search_query=integral+calculus+indefinite+definite+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Indefinite/definite integrals, substitution, by parts, partial fractions, properties."},
        {"title": "Integration | Mohit Tyagi", "url": "https://www.youtube.com/results?search_query=integral+calculus+mohit+tyagi+jee+advanced", "platform": "youtube", "teacher": "Mohit Tyagi (Competishun)", "why": "Advanced integration, reduction formulas, Leibnitz rule."},
    ],
    "differential equations": [
        {"title": "Differential Equations | Physics Wallah", "url": "https://www.youtube.com/results?search_query=differential+equations+one+shot+physics+wallah+jee", "platform": "youtube", "teacher": "Physics Wallah", "why": "Variable separable, homogeneous, linear DE, Bernoulli, orthogonal trajectories, growth-decay."},
    ],
    # ===================== UPSC / CSE =====================
    "indian polity": [
        {"title": "Indian Polity Complete M. Laxmikanth | Study IQ", "url": "https://www.youtube.com/results?search_query=indian+polity+m+laxmikanth+study+iq+upsc+full+lecture", "platform": "youtube", "teacher": "Study IQ (Dr. Vipan Goyal)", "why": "Complete Laxmikanth polity for UPSC Prelims + Mains."},
        {"title": "Indian Polity by Khan Sir", "url": "https://www.youtube.com/results?search_query=indian+polity+khan+sir+upsc+complete", "platform": "youtube", "teacher": "Khan Sir (Khan GS Research Centre)", "why": "Simple Hindi+English explanation; extremely popular for UPSC/State PSCs."},
        {"title": "Indian Polity | OnlyIAS (Suhail Sir)", "url": "https://www.youtube.com/results?search_query=indian+polity+onlyias+upsc+complete+lectures", "platform": "youtube", "teacher": "OnlyIAS", "why": "UPSC CSE-focused polity with PYQ analysis."},
        {"title": "Polity for UPSC | VisionIAS", "url": "https://www.youtube.com/results?search_query=vision+ias+polity+lectures+upsc", "platform": "youtube", "teacher": "VisionIAS", "why": "Foundation course polity from premier UPSC institute."},
    ],
    "indian economy": [
        {"title": "Indian Economy for UPSC | Study IQ (Rahul Meena)", "url": "https://www.youtube.com/results?search_query=indian+economy+study+iq+upsc+mrunal+complete+lectures", "platform": "youtube", "teacher": "Study IQ / Mrunal Patel", "why": "Planning, Budget, RBI, Agriculture, Industry, Banking, UPSC-focused."},
        {"title": "Indian Economy by Mrunal Patel (Win CSE)", "url": "https://www.youtube.com/results?search_query=mrunal+patel+indian+economy+upsc+win+cse+playlist", "platform": "youtube", "teacher": "Mrunal Patel", "why": "Win CSE series — legendary economy lectures for UPSC."},
        {"title": "Economy | Khan Sir", "url": "https://www.youtube.com/results?search_query=indian+economy+khan+sir+upsc", "platform": "youtube", "teacher": "Khan Sir", "why": "Simple Hinglish economy for UPSC/SSC/Banking."},
    ],
    "modern indian history": [
        {"title": "Modern Indian History (1857-1947) | Study IQ", "url": "https://www.youtube.com/results?search_query=modern+indian+history+1857+1947+study+iq+upsc+one+shot", "platform": "youtube", "teacher": "Study IQ", "why": "1857-1947 freedom struggle, Governor Generals, movements for UPSC Prelims."},
        {"title": "Modern History | OnlyIAS", "url": "https://www.youtube.com/results?search_query=modern+history+onlyias+upsc+complete+spectrum", "platform": "youtube", "teacher": "OnlyIAS", "why": "Spectrum Modern India book-based lectures."},
        {"title": "Modern History by Khan Sir", "url": "https://www.youtube.com/results?search_query=modern+history+khan+sir+upsc+freedom+struggle", "platform": "youtube", "teacher": "Khan Sir", "why": "Engaging Hinglish lectures on the freedom struggle."},
    ],
    "ancient history": [
        {"title": "Ancient Indian History | Study IQ", "url": "https://www.youtube.com/results?search_query=ancient+indian+history+study+iq+upsc+complete+rs+sharma", "platform": "youtube", "teacher": "Study IQ", "why": "Indus Valley, Vedic, Maurya, Gupta empires for UPSC (RS Sharma-based)."},
    ],
    "medieval history": [
        {"title": "Medieval Indian History | Study IQ", "url": "https://www.youtube.com/results?search_query=medieval+indian+history+study+iq+upsc+complete", "platform": "youtube", "teacher": "Study IQ", "why": "Delhi Sultanate, Mughal Empire, Vijayanagara, Bahamani kingdoms."},
    ],
    "indian geography": [
        {"title": "Indian Geography for UPSC | Amit Sengupta / Study IQ", "url": "https://www.youtube.com/results?search_query=indian+geography+upsc+prelims+study+iq+complete+lectures", "platform": "youtube", "teacher": "Amit Sengupta / Study IQ", "why": "Physical, economic, social geography of India, NCERT-based."},
        {"title": "Geography | OnlyIAS", "url": "https://www.youtube.com/results?search_query=indian+geography+onlyias+upsc+ncert", "platform": "youtube", "teacher": "OnlyIAS", "why": "NCERT + GC Leong-based geography for UPSC."},
    ],
    "world geography": [
        {"title": "World Geography | Study IQ", "url": "https://www.youtube.com/results?search_query=world+geography+study+iq+upsc", "platform": "youtube", "teacher": "Study IQ", "why": "Continents, oceans, mountains, rivers, climate for UPSC Prelims."},
    ],
    "environment": [
        {"title": "Environment & Ecology for UPSC | Study IQ", "url": "https://www.youtube.com/results?search_query=environment+ecology+upsc+prelims+study+iq+shankar+ias", "platform": "youtube", "teacher": "Study IQ", "why": "Ecosystems, biodiversity, climate change, conventions — Shankar IAS book-based."},
        {"title": "Environment | OnlyIAS", "url": "https://www.youtube.com/results?search_query=environment+ecology+onlyias+upsc", "platform": "youtube", "teacher": "OnlyIAS", "why": "UPSC Prelims-focused environment with current affairs."},
    ],
    "science technology": [
        {"title": "Science & Technology for UPSC | Study IQ", "url": "https://www.youtube.com/results?search_query=science+technology+upsc+study+iq+one+shot", "platform": "youtube", "teacher": "Study IQ", "why": "Biotech, IT, Space, Defense, Nuclear tech for UPSC Prelims."},
    ],
    "current affairs": [
        {"title": "Daily Current Affairs | Study IQ", "url": "https://www.youtube.com/@StudyIQeducation", "platform": "youtube", "teacher": "Study IQ", "why": "Daily news analysis for UPSC Prelims + Mains; most popular UPSC current affairs channel."},
        {"title": "Daily Current Affairs | OnlyIAS", "url": "https://www.youtube.com/@OnlyIAS", "platform": "youtube", "teacher": "OnlyIAS", "why": "Daily news + editorial analysis for UPSC."},
        {"title": "Daily News Analysis | VisionIAS", "url": "https://www.youtube.com/results?search_query=vision+ias+daily+news+analysis", "platform": "youtube", "teacher": "VisionIAS", "why": "Premium daily current affairs from VisionIAS."},
    ],
    "ethics": [
        {"title": "Ethics (GS Paper 4) | Study IQ", "url": "https://www.youtube.com/results?search_query=ethics+integrity+aptitude+study+iq+upsc+mains", "platform": "youtube", "teacher": "Study IQ", "why": "Ethics, integrity, aptitude for UPSC Mains GS Paper 4."},
    ],
    "csat": [
        {"title": "CSAT for UPSC | Study IQ / Gaurav Sir", "url": "https://www.youtube.com/results?search_query=csat+upsc+study+iq+quantitative+aptitude+reasoning", "platform": "youtube", "teacher": "Study IQ", "why": "Maths, reasoning, comprehension for CSAT Paper 2 with tricks."},
    ],
    # ===================== SSC / BANKING / RAILWAY =====================
    "ssc": [
        {"title": "SSC Complete Preparation | Adda247", "url": "https://www.youtube.com/results?search_query=ssc+cgl+complete+preparation+adda247+maths+reasoning+english", "platform": "youtube", "teacher": "Adda247", "why": "Maths, reasoning, English, GK for SSC CGL/CHSL/CPO/MTS."},
        {"title": "SSC Maths | Rakesh Yadav Sir", "url": "https://www.youtube.com/results?search_query=ssc+maths+rakesh+yadav+one+shot", "platform": "youtube", "teacher": "Rakesh Yadav Sir", "why": "Legendary SSC maths teacher with concept + short tricks."},
        {"title": "SSC by Khan Sir", "url": "https://www.youtube.com/results?search_query=ssc+cgl+khan+sir+gs+complete", "platform": "youtube", "teacher": "Khan Sir", "why": "GS/GK for SSC in simple Hinglish."},
        {"title": "SSC English | Jaideep Sir", "url": "https://www.youtube.com/results?search_query=ssc+english+jaideep+sir+vocabulary+grammar", "platform": "youtube", "teacher": "Jaideep Sir", "why": "Complete English preparation for SSC exams."},
    ],
    "quantitative aptitude": [
        {"title": "Quantitative Aptitude for Bank/SSC | Adda247", "url": "https://www.youtube.com/results?search_query=quantitative+aptitude+bank+ssc+adda247+one+shot", "platform": "youtube", "teacher": "Adda247", "why": "Complete quants for banking, SSC, railways with short tricks."},
    ],
    "reasoning": [
        {"title": "Reasoning for All Competitive Exams | Adda247", "url": "https://www.youtube.com/results?search_query=reasoning+all+competitive+exams+adda247+puzzle", "platform": "youtube", "teacher": "Adda247 (Saurav Singh)", "why": "Logical reasoning, puzzles, coding-decoding, series, direction, blood relations."},
        {"title": "Reasoning Tricks | Deepak Tirthyani", "url": "https://www.youtube.com/results?search_query=reasoning+tricks+deepak+tirthyani+ssc+bank", "platform": "youtube", "teacher": "Deepak Tirthyani", "why": "Short tricks for SSC, Banking, Railway reasoning."},
    ],
    # ===================== NDA / CDS / DEFENCE =====================
    "nda": [
        {"title": "NDA Complete Preparation | Physics Wallah (Defence Wallah)", "url": "https://www.youtube.com/results?search_query=nda+exam+preparation+physics+wallah+defence+wallah", "platform": "youtube", "teacher": "Defence Wallah (PW)", "why": "Maths, GAT, English for NDA/NA examination."},
        {"title": "NDA Maths | Arpit Sir (Unacademy)", "url": "https://www.youtube.com/results?search_query=nda+maths+unacademy+arpit+sir", "platform": "youtube", "teacher": "Unacademy NDA", "why": "NDA-specific mathematics with PYQs and tricks."},
    ],
    "cds": [
        {"title": "CDS Exam Preparation | Unacademy CDS", "url": "https://www.youtube.com/results?search_query=cds+exam+preparation+unacademy+english+maths+gk", "platform": "youtube", "teacher": "Unacademy CDS/AFCAT", "why": "CDS/AFCAT English, Maths, GK full preparation."},
    ],
    # ===================== TEACHING EXAMS =====================
    "ctet": [
        {"title": "CTET Complete Preparation | Himanshi Singh", "url": "https://www.youtube.com/results?search_query=ctet+preparation+himanshi+singh+complete", "platform": "youtube", "teacher": "Himanshi Singh (Let's LEARN)", "why": "CTET CDP, EVS, Maths, Hindi, English, SST pedagogy; most trusted CTET teacher."},
        {"title": "CTET by Adda247", "url": "https://www.youtube.com/results?search_query=ctet+adda247+classes", "platform": "youtube", "teacher": "Teachers Adda (Adda247)", "why": "Complete CTET Paper 1 and Paper 2 preparation."},
    ],
    # ===================== STATE PSCs (BPSC / UPPSC / MPSC / RAS) =====================
    "bpsc": [
        {"title": "BPSC Complete Preparation | Khan Sir / Khan GS", "url": "https://www.youtube.com/results?search_query=bpsc+preparation+khan+sir+complete+lecture+bihar+pcs", "platform": "youtube", "teacher": "Khan Sir (Khan GS)", "why": "Bihar PSC complete GS preparation in Hinglish; Bihar-specific content."},
        {"title": "BPSC 70+ | Study IQ", "url": "https://www.youtube.com/results?search_query=bpsc+70th+study+iq+preparation+strategy", "platform": "youtube", "teacher": "Study IQ", "why": "BPSC Prelims + Mains strategy and content."},
    ],
    "uppsc": [
        {"title": "UPPSC Preparation | Khan Sir / Study IQ", "url": "https://www.youtube.com/results?search_query=uppsc+uppcs+preparation+khan+sir+study+iq", "platform": "youtube", "teacher": "Khan Sir / Study IQ", "why": "UP PCS Prelims + Mains with UP-specific GK."},
    ],
    "mpsc": [
        {"title": "MPSC Preparation | Study IQ / MPSC Wallah", "url": "https://www.youtube.com/results?search_query=mpsc+maharashtra+pcs+preparation+lectures", "platform": "youtube", "teacher": "MPSC Wallah / Adda247", "why": "Maharashtra PSC Rajyaseva Prelims + Mains."},
    ],
    "ras": [
        {"title": "RAS/RPSC Preparation | Study IQ / Utkarsh Classes", "url": "https://www.youtube.com/results?search_query=ras+rpsc+rajasthan+pcs+preparation+utkarsh+classes", "platform": "youtube", "teacher": "Utkarsh Classes", "why": "Rajasthan Administrative Services with Rajasthan-specific GK."},
    ],
    # ===================== HINDI MEDIUM GENERAL =====================
    "hindi": [
        {"title": "All Competitive Exams GS | Khan Sir", "url": "https://www.youtube.com/results?search_query=khan+sir+gs+complete+hindi+medium", "platform": "youtube", "teacher": "Khan Sir (Khan GS)", "why": "Hindi medium GS/GK for UPSC, BPSC, UPPSC, SSC, Railway."},
        {"title": "Hindi Literature / Grammar | Magnet Brains", "url": "https://www.youtube.com/results?search_query=hindi+grammar+magnet+brains+class+10+12", "platform": "youtube", "teacher": "Magnet Brains", "why": "Hindi grammar and literature for CBSE/State boards."},
        {"title": "Hindi for Competitive Exams | Rukmani Prakashan / Nitin Sir", "url": "https://www.youtube.com/results?search_query=hindi+competitive+exam+nitin+gupta+sir", "platform": "youtube", "teacher": "Nitin Gupta Sir", "why": "Hindi for SSC, Bank, Railway, UPSC, State PSC."},
    ],
    # ===================== CBSE / CLASS 10 / 12 / BOARDS =====================
    "class 10": [
        {"title": "Class 10 All Subjects Full Course FREE | Magnet Brains", "url": "https://www.youtube.com/results?search_query=class+10+all+subjects+magnet+brains+full+chapter+numericals", "platform": "youtube", "teacher": "Magnet Brains", "why": "BEST free Class 10 NCERT line-by-line explanation for CBSE/BSEB/UP Board all subjects (Maths, Science, SST, English, Hindi)."},
        {"title": "Class 10 Maths + Science | Physics Wallah Udaan Batch", "url": "https://www.youtube.com/results?search_query=class+10+physics+wallah+udaan+batch+full+course", "platform": "youtube", "teacher": "Physics Wallah Udaan", "why": "Complete Class 10 CBSE board prep with PYQ practice and numerical solving."},
        {"title": "Class 10 SST | Magnet Brains Social Science", "url": "https://www.youtube.com/results?search_query=class+10+social+science+magnet+brains+history+civics+geography+economics+full+chapter", "platform": "youtube", "teacher": "Magnet Brains", "why": "Complete Class 10 History/Geography/Civics/Economics NCERT explanation in Hindi."},
        {"title": "Class 10 Science | Vedantu CBSE", "url": "https://www.youtube.com/results?search_query=class+10+science+vedantu+one+shot+full+chapter+numericals", "platform": "youtube", "teacher": "Vedantu", "why": "CBSE board exam focused Science chapters with NCERT question answers."},
        {"title": "Class 10 Hindi Grammar | Magnet Brains", "url": "https://www.youtube.com/results?search_query=class+10+hindi+grammar+magnet+brains+course+b", "platform": "youtube", "teacher": "Magnet Brains", "why": "Hindi vyakaran (रस, अलंकार, संधि, समास, वाक्य) for CBSE/BSEB/UP Board."},
    ],
    "class 11": [
        {"title": "Class 11 Full Syllabus | Physics Wallah Arjuna Batch", "url": "https://www.youtube.com/results?search_query=class+11+physics+wallah+arjuna+batch+full+chapter", "platform": "youtube", "teacher": "Physics Wallah Arjuna", "why": "Complete Class 11 PCMB for CBSE + JEE/NEET foundation."},
        {"title": "Class 11 NCERT | Magnet Brains", "url": "https://www.youtube.com/results?search_query=class+11+magnet+brains+physics+chemistry+maths+biology+full+chapter", "platform": "youtube", "teacher": "Magnet Brains", "why": "Free NCERT-focused Class 11 all subjects for board exam prep."},
    ],
    "class 12": [
        {"title": "Class 12 Board Exam Preparation | Physics Wallah Lakshya Batch", "url": "https://www.youtube.com/results?search_query=class+12+physics+wallah+lakshya+batch+board+exam", "platform": "youtube", "teacher": "Physics Wallah Lakshya", "why": "Complete Class 12 CBSE board prep + JEE/NEET."},
        {"title": "Class 12 NCERT PYQs & Sample Papers | CBSE Class Videos", "url": "https://www.youtube.com/results?search_query=class+12+cbse+sample+paper+solutions+2024-25+physics+chemistry+maths+biology", "platform": "youtube", "teacher": "CBSE Class Videos / Various", "why": "Previous year CBSE board questions and latest sample papers with full solutions."},
        {"title": "Class 12 NCERT Full Chapter | Magnet Brains", "url": "https://www.youtube.com/results?search_query=class+12+magnet+brains+physics+chemistry+biology+maths+full+chapter", "platform": "youtube", "teacher": "Magnet Brains", "why": "NCERT line-by-line explanation in Hindi + English for board exams."},
    ],
    "cbse": [
        {"title": "CBSE Official Website (Sample Papers, Syllabus)", "url": "https://cbseacademic.nic.in/", "platform": "cbse", "teacher": "CBSE Academic", "why": "Official CBSE curriculum, sample question papers (SQP), marking scheme for current year."},
        {"title": "NCERT Books FREE Download", "url": "https://ncert.nic.in/textbook.php", "platform": "ncert", "teacher": "NCERT", "why": "ALL NCERT textbooks free PDF download — the single most important source for CBSE and most state boards."},
    ],
    "bseb": [
        {"title": "Bihar Board Class 10/12 | Khan Sir / Khan GS + Magnet Brains", "url": "https://www.youtube.com/results?search_query=bihar+board+class+10+12+khan+sir+magnet+brains+model+paper+solution", "platform": "youtube", "teacher": "Khan Sir, Magnet Brains", "why": "BSEB Hindi-medium content, model paper solutions, objective question banks."},
        {"title": "Bihar Board Official (BSEB)", "url": "http://biharboardonline.bihar.gov.in/", "platform": "bseb", "teacher": "BSEB Official", "why": "Bihar Board official website for syllabus, model papers, results."},
    ],
    "up board": [
        {"title": "UP Board Class 10/12 | Magnet Brains Hindi Medium", "url": "https://www.youtube.com/results?search_query=up+board+class+10+12+magnet+brains+hindi+medium+full+chapter", "platform": "youtube", "teacher": "Magnet Brains", "why": "UP Board NCERT-based lectures in Hindi medium (गणित, विज्ञान, सामाजिक विज्ञान)."},
        {"title": "UPMSP Official Website", "url": "https://upmsp.edu.in/", "platform": "upmsp", "teacher": "UPMSP Official", "why": "UP Board official syllabus, model papers, exam dates."},
    ],
    "icse": [
        {"title": "ICSE / ISC Class 10 / 12 | Clarify Knowledge", "url": "https://www.youtube.com/results?search_query=icse+class+10+all+subjects+clarify+knowledge+one+shot+full+chapter", "platform": "youtube", "teacher": "Clarify Knowledge", "why": "ICSE Class 10 full syllabus free (Maths, Physics, Chem, Bio, History, English)."},
        {"title": "ISC Class 12 | Clarify Knowledge / Sir Tarun Rupani", "url": "https://www.youtube.com/results?search_query=isc+class+12+clarify+knowledge+maths+physics+chemistry+biology+full+chapter", "platform": "youtube", "teacher": "Clarify Knowledge, Sir Tarun Rupani", "why": "ISC Class 12 board exam focused lectures and paper solutions."},
    ],
    "board exam": [
        {"title": "NCERT Official — FREE Textbooks (all classes/subjects)", "url": "https://ncert.nic.in/textbook.php", "platform": "ncert", "teacher": "NCERT", "why": "DOWNLOAD ALL NCERT BOOKS FREE PDF — every Indian board follows NCERT."},
        {"title": "Exam Fear Education (No.1 FREE education for Classes 6-12)", "url": "https://www.youtube.com/results?search_query=exam+fear+education+class+10+12+physics+chemistry+maths+biology+one+shot", "platform": "youtube", "teacher": "Exam Fear Education (Roshni Mam)", "why": "100% free Class 6-12 all subjects with detailed NCERT explanations."},
    ],
    # ===================== COLLEGE / UNIVERSITY (BTech / BSc / MBBS / BCom / LLB) =====================
    "engineering mathematics": [
        {"title": "Engineering Mathematics | Neso Academy", "url": "https://www.youtube.com/results?search_query=engineering+mathematics+neso+academy+full+course", "platform": "youtube", "teacher": "Neso Academy", "why": "Linear algebra, calculus, differential equations, complex analysis — complete BTech math."},
        {"title": "Engineering Maths | Gate Smashers", "url": "https://www.youtube.com/results?search_query=engineering+mathematics+gate+smashers+one+shot", "platform": "youtube", "teacher": "Gate Smashers", "why": "GATE-focused engineering maths with PYQs and short tricks."},
        {"title": "Higher Engineering Mathematics | 5 Minutes Engineering", "url": "https://www.youtube.com/results?search_query=higher+engineering+mathematics+5+minutes+engineering", "platform": "youtube", "teacher": "5 Minutes Engineering", "why": "BTech semester-wise math lectures in simple Hindi/English."},
    ],
    "data structures": [
        {"title": "Data Structures & Algorithms (DSA) | Gate Smashers", "url": "https://www.youtube.com/results?search_query=data+structures+algorithms+gate+smashers+full+course", "platform": "youtube", "teacher": "Gate Smashers", "why": "Complete DSA for BTech CSE/IT with C++/Java examples."},
        {"title": "DSA Full Course | Neso Academy", "url": "https://www.youtube.com/results?search_query=data+structures+neso+academy+c+language", "platform": "youtube", "teacher": "Neso Academy", "why": "Arrays, linked lists, trees, graphs, sorting, searching — all DSA topics."},
        {"title": "Data Structures | Knowledge Gate (Saurabh Shukla)", "url": "https://www.youtube.com/results?search_query=data+structures+knowledge+gate+saurabh+shukla", "platform": "youtube", "teacher": "Knowledge Gate (Saurabh Shukla)", "why": "Deep concept clarity on DSA in C/C++ — highly rated by BTech students."},
        {"title": "Algorithms | Abdul Bari", "url": "https://www.youtube.com/results?search_query=abdul+bari+algorithms+full+course", "platform": "youtube", "teacher": "Abdul Bari", "why": "Legendary algorithm lectures — recursion, DP, greedy, graph algorithms."},
    ],
    "dsa": [
        {"title": "DSA Complete | CodeWithHarry", "url": "https://www.youtube.com/results?search_query=data+structures+algorithms+codewithharry", "platform": "youtube", "teacher": "CodeWithHarry", "why": "Hindi DSA course with Python/C++ for beginners."},
        {"title": "DSA GATE | Gate Smashers", "url": "https://www.youtube.com/results?search_query=gate+smashers+data+structures+full+playlist", "platform": "youtube", "teacher": "Gate Smashers", "why": "GATE/University exam oriented DSA."},
    ],
    "digital electronics": [
        {"title": "Digital Electronics | Neso Academy", "url": "https://www.youtube.com/results?search_query=digital+electronics+neso+academy+full+course", "platform": "youtube", "teacher": "Neso Academy", "why": "Boolean algebra, logic gates, flip-flops, counters, ADC/DAC — BTech ECE/EE/CSE."},
        {"title": "Digital Logic | Gate Smashers", "url": "https://www.youtube.com/results?search_query=digital+logic+design+gate+smashers", "platform": "youtube", "teacher": "Gate Smashers", "why": "GATE-oriented digital electronics with K-maps and sequential circuits."},
    ],
    "signals systems": [
        {"title": "Signals and Systems | Neso Academy", "url": "https://www.youtube.com/results?search_query=signals+and+systems+neso+academy", "platform": "youtube", "teacher": "Neso Academy", "why": "Fourier, Laplace, Z-transform, convolution for BTech ECE/EE."},
        {"title": "Signals & Systems | Gate Smashers", "url": "https://www.youtube.com/results?search_query=signals+systems+gate+smashers+one+shot", "platform": "youtube", "teacher": "Gate Smashers", "why": "GATE/University exam signal & systems revision."},
    ],
    "operating system": [
        {"title": "Operating Systems | Gate Smashers", "url": "https://www.youtube.com/results?search_query=operating+systems+gate+smashers+full+course", "platform": "youtube", "teacher": "Gate Smashers", "why": "Processes, threads, scheduling, memory management, deadlocks, file systems."},
        {"title": "OS | Knowledge Gate (Saurabh Shukla)", "url": "https://www.youtube.com/results?search_query=operating+system+knowledge+gate+saurabh+shukla", "platform": "youtube", "teacher": "Knowledge Gate", "why": "Detailed OS concepts for BTech and GATE."},
    ],
    "dbms": [
        {"title": "DBMS | Gate Smashers", "url": "https://www.youtube.com/results?search_query=dbms+gate+smashers+full+course", "platform": "youtube", "teacher": "Gate Smashers", "why": "ER model, normalization, SQL, transactions, concurrency control."},
        {"title": "Database Management | Neso Academy", "url": "https://www.youtube.com/results?search_query=dbms+neso+academy+full+playlist", "platform": "youtube", "teacher": "Neso Academy", "why": "Complete DBMS for BTech CSE/IT."},
        {"title": "DBMS | Knowledge Gate", "url": "https://www.youtube.com/results?search_query=dbms+knowledge+gate+saurabh+shukla", "platform": "youtube", "teacher": "Knowledge Gate", "why": "Normalization, SQL, transactions in depth."},
    ],
    "computer networks": [
        {"title": "Computer Networks | Gate Smashers", "url": "https://www.youtube.com/results?search_query=computer+networks+gate+smashers+full+course", "platform": "youtube", "teacher": "Gate Smashers", "why": "OSI/TCP model, routing, IP addressing, transport layer — BTech/GATE."},
        {"title": "CN | Neso Academy", "url": "https://www.youtube.com/results?search_query=computer+networks+neso+academy", "platform": "youtube", "teacher": "Neso Academy", "why": "Layer-by-layer networking with clear diagrams."},
    ],
    "basic electrical engineering": [
        {"title": "Basic Electrical Engineering | Neso Academy", "url": "https://www.youtube.com/results?search_query=basic+electrical+engineering+neso+academy", "platform": "youtube", "teacher": "Neso Academy", "why": "KVL, KCL, AC/DC circuits, transformers, machines — BTech 1st year."},
        {"title": "BEE | 5 Minutes Engineering", "url": "https://www.youtube.com/results?search_query=basic+electrical+engineering+5+minutes+engineering", "platform": "youtube", "teacher": "5 Minutes Engineering", "why": "Hindi/English BTech 1st year electrical lectures."},
        {"title": "Electrical Engineering | Saurabh Shukla (Knowledge Gate)", "url": "https://www.youtube.com/results?search_query=basic+electrical+engineering+knowledge+gate+sir", "platform": "youtube", "teacher": "Knowledge Gate", "why": "Network theory, circuits, machines for BTech first year."},
    ],
    "engineering physics": [
        {"title": "Engineering Physics | Neso Academy", "url": "https://www.youtube.com/results?search_query=engineering+physics+neso+academy+quantum+mechanics", "platform": "youtube", "teacher": "Neso Academy", "why": "Quantum mechanics, solid state physics, optics for BTech 1st year."},
        {"title": "BTech Physics | 5 Minutes Engineering", "url": "https://www.youtube.com/results?search_query=engineering+physics+5+minutes+engineering+btch", "platform": "youtube", "teacher": "5 Minutes Engineering", "why": "Semester-wise BTech applied physics."},
    ],
    "bsc physics": [
        {"title": "BSc Physics | Physics Wallah Degree", "url": "https://www.youtube.com/results?search_query=bsc+physics+physics+wallah+degree+one+shot", "platform": "youtube", "teacher": "Physics Wallah (Degree)", "why": "Mechanics, thermodynamics, optics, electromagnetism for BSc."},
        {"title": "Physics Honours | Neso Academy", "url": "https://www.youtube.com/results?search_query=bsc+physics+honours+neso+academy+classical+mechanics", "platform": "youtube", "teacher": "Neso Academy", "why": "University-level physics lectures."},
    ],
    "mbbs anatomy": [
        {"title": "MBBS Anatomy | Rajesh Kaushal (PW MedEd)", "url": "https://www.youtube.com/results?search_query=mbbs+anatomy+rajesh+kaushal+pw+meded", "platform": "youtube", "teacher": "Rajesh Kaushal (PW MedEd)", "why": "Gross anatomy, neuroanatomy, embryology for MBBS 1st year."},
        {"title": "Anatomy | Dr. Najeeb Lectures", "url": "https://www.youtube.com/results?search_query=dr+najeeb+anatomy+lectures+mbbs", "platform": "youtube", "teacher": "Dr. Najeeb", "why": "World-famous medical lectures with hand-drawn diagrams."},
        {"title": "MBBS 1st Year | Physics Wallah MedEd", "url": "https://www.youtube.com/results?search_query=mbbs+first+year+physics+wallah+meded+lectures", "platform": "youtube", "teacher": "PW MedEd", "why": "Anatomy, Physiology, Biochemistry for MBBS Phase I."},
    ],
    "mbbs physiology": [
        {"title": "Physiology | Dr. Najeeb", "url": "https://www.youtube.com/results?search_query=dr+najeeb+physiology+mbbs+lectures", "platform": "youtube", "teacher": "Dr. Najeeb", "why": "Cardiovascular, respiratory, renal, neuro physiology explained in depth."},
        {"title": "MBBS Physiology | PW MedEd", "url": "https://www.youtube.com/results?search_query=physiology+mbbs+pw+meded+one+shot", "platform": "youtube", "teacher": "PW MedEd", "why": "MBBS-focused physiology with clinical correlations."},
    ],
    "mbbs biochemistry": [
        {"title": "Biochemistry | Dr. Najeeb", "url": "https://www.youtube.com/results?search_query=dr+najeeb+biochemistry+metabolism", "platform": "youtube", "teacher": "Dr. Najeeb", "why": "Metabolism cycles, enzymes, molecular biology for MBBS."},
        {"title": "Biochemistry MBBS | PW MedEd", "url": "https://www.youtube.com/results?search_query=biochemistry+mbbs+pw+meded+lecture", "platform": "youtube", "teacher": "PW MedEd", "why": "MBBS-oriented biochemistry with clinical cases."},
    ],
    "accounting": [
        {"title": "Financial Accounting | Rajat Arora (BA BCom)", "url": "https://www.youtube.com/results?search_query=financial+accounting+rajat+arora+bcom+lectures", "platform": "youtube", "teacher": "Rajat Arora", "why": "Journal entries, ledger, trial balance, final accounts for BCom/BBA."},
        {"title": "Accounting for BCom | CA Wallah (PW)", "url": "https://www.youtube.com/results?search_query=ca+wallah+physics+wallah+accounts+bcom", "platform": "youtube", "teacher": "CA Wallah (PW)", "why": "BCom/MCom accounts, cost accounting, financial management."},
        {"title": "Class 11-12 / BCom Accounts | Magnet Brains", "url": "https://www.youtube.com/results?search_query=accounts+magnet+brains+bcom+class+11", "platform": "youtube", "teacher": "Magnet Brains", "why": "Complete accounting from basics to BCom level in Hindi."},
    ],
    "business law": [
        {"title": "Business Law / Company Law | Law Wallah (PW)", "url": "https://www.youtube.com/results?search_query=business+law+law+wallah+physics+wallah+bcom", "platform": "youtube", "teacher": "Law Wallah (PW)", "why": "Indian Contract Act, Companies Act, Sale of Goods Act for BCom/BBALLB."},
        {"title": "Law Lectures | Legal Bites / NLSIU", "url": "https://www.youtube.com/results?search_query=indian+contract+act+legal+bites+lectures", "platform": "youtube", "teacher": "Legal Bites Academy", "why": "Comprehensive law lectures for LLB/ judiciary aspirants."},
    ],
    "law of torts": [
        {"title": "Law of Torts | Law Wallah (PW)", "url": "https://www.youtube.com/results?search_query=law+of+torts+law+wallah+anand+sir", "platform": "youtube", "teacher": "Law Wallah (PW)", "why": "Tort law, negligence, nuisance, defamation for LLB."},
        {"title": "Jurisprudence & Torts | Legal Bites", "url": "https://www.youtube.com/results?search_query=law+of+torts+legal+bites+full+lecture", "platform": "youtube", "teacher": "Legal Bites Academy", "why": "LLB-focused tort law with case examples."},
    ],
    "constitutional law": [
        {"title": "Constitutional Law of India | Law Wallah (PW)", "url": "https://www.youtube.com/results?search_query=constitutional+law+india+law+wallah+ba+llb", "platform": "youtube", "teacher": "Law Wallah (PW)", "why": "Indian Constitution, fundamental rights, directive principles for LLB."},
        {"title": "Constitution | Finology Legal", "url": "https://www.youtube.com/results?search_query=constitutional+law+india+finology+legal+llb", "platform": "youtube", "teacher": "Finology Legal", "why": "Simplified constitutional law with landmark judgments."},
    ],
    "microeconomics": [
        {"title": "Microeconomics | Rajat Arora / Economics Wallah", "url": "https://www.youtube.com/results?search_query=microeconomics+one+shot+rajat+arora+bcom", "platform": "youtube", "teacher": "Rajat Arora", "why": "Demand, supply, consumer behavior, market structures for BCom/BA."},
        {"title": "Economics | Khan Academy India", "url": "https://www.khanacademy.org/economics-finance-domain", "platform": "khanacademy", "teacher": "Khan Academy", "why": "Free, world-class micro & macro economics lessons."},
    ],
    "thermodynamics engineering": [
        {"title": "Engineering Thermodynamics | Neso Academy", "url": "https://www.youtube.com/results?search_query=engineering+thermodynamics+neso+academy", "platform": "youtube", "teacher": "Neso Academy", "why": "Laws, cycles, entropy, availability for BTech ME/CH."},
        {"title": "Thermodynamics | 5 Minutes Engineering", "url": "https://www.youtube.com/results?search_query=thermodynamics+engineering+5+minutes+engineering", "platform": "youtube", "teacher": "5 Minutes Engineering", "why": "Simple Hindi/English lectures on thermo cycles (Rankine, Otto, Diesel)."},
    ],
}


def _word_signature(s: str) -> set:
    """Extract significant words from a string (length > 2, not common stop words)."""
    import re
    stop = {"the","a","an","of","in","on","at","to","for","and","or",
            "with","by","from","class","jee","neet","one","shot","full",
            "chapter","physics","biology","chemistry","maths","math",
            "lecture","crash","course","upsc","iit","aiims","exam",
            "complete","ncert","all","part","level","problems","pyq",
            "pyqs","most","important","best","detailed","concepts","basic",
            "advanced","foundation","board","cbse","icse","cse","prelims",
            "mains","paper","grade","students","student","indian","&"}
    return {w for w in re.sub(r'[^a-z0-9 ]+', ' ', s.lower()).split() if len(w) > 2 and w not in stop}


def _match_curated(chapter_title: str) -> List[dict]:
    """Return curated resources if the chapter title matches known topics.
    Uses word-overlap scoring to match multi-word keywords.
    Returns up to 4 resources for richer learning.
    """
    ch_words = _word_signature(chapter_title)
    scored_resources = {}  # url -> (best_score, resource_dict)

    for keyword, resources in CURATED_RESOURCES.items():
        kw_words = _word_signature(keyword)
        if not kw_words:
            continue
        kw_phrase = keyword.lower()
        title_lower = chapter_title.lower()
        # Direct substring match = very strong signal
        if kw_phrase in title_lower:
            score = 100
        else:
            # Word overlap: require at least half of keyword's significant words to appear
            overlap = ch_words & kw_words
            ratio = len(overlap) / len(kw_words)
            if ratio < 0.5 and len(overlap) < 1:
                continue
            score = int(ratio * 50) + len(overlap) * 5
        for r in resources:
            url = r["url"]
            if url not in scored_resources or score > scored_resources[url][0]:
                scored_resources[url] = (score, r)

    # Sort by score descending, take top 4
    ranked = sorted(scored_resources.values(), key=lambda x: -x[0])
    out = []
    seen_titles = set()
    for score, r in ranked:
        if score < 5:
            continue
        # Dedup by URL and near-duplicate titles
        title_key = r["title"][:40].lower()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        out.append(r)
        if len(out) >= 4:
            break
    return out


def _ddg_search(query: str, max_results: int = 4) -> List[dict]:
    """Run a DuckDuckGo search and return results as dicts. Tries video search first."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            is_video = any(kw in query.lower() for kw in ('youtube','lecture','video','one shot','tutorial'))
            if is_video:
                try:
                    for hit in ddgs.videos(query, max_results=max_results):
                        url = hit.get("href","") or hit.get("content","")
                        title = hit.get("title","")
                        body = hit.get("description","")
                        channel = hit.get("uploader","") or hit.get("channel","")
                        results.append({
                            "title": title, "url": url, "platform": "youtube",
                            "teacher": channel,
                            "why": (body or f"Video lecture on {query[:80]}")[:200],
                        })
                except Exception as e:
                    logger.debug(f"DDG video search failed: {e}")
            if len(results) < 2:
                for hit in ddgs.text(query, max_results=max_results):
                    url = hit.get("href","")
                    title = hit.get("title","")
                    body = hit.get("body","")
                    url_l = url.lower()
                    platform = "youtube" if "youtube.com" in url_l or "youtu.be" in url_l else (
                        "nptel" if "nptel" in url_l else (
                            "khanacademy" if "khanacademy" in url_l else (
                                "vedantu" if "vedantu" in url_l else (
                                    "pw" if any(x in url_l for x in ("physicswallah","pw.live")) else (
                                        "unacademy" if "unacademy" in url_l else (
                                            "byjus" if "byjus" in url_l else "other"))))))
                    teacher = ""
                    if platform == "youtube":
                        for sep in ("|","-","–","—"):
                            if sep in title:
                                parts = title.split(sep)
                                teacher = parts[-1].strip()
                                if len(teacher) > 50:
                                    teacher = teacher[:50]
                                break
                    elif platform in ("khanacademy","vedantu","nptel","pw","unacademy","byjus"):
                        teacher = platform.title()
                    results.append({
                        "title": title, "url": url, "platform": platform,
                        "teacher": teacher,
                        "why": body[:200] if body else f"Resource for: {query[:80]}",
                    })
        return results
    except Exception as e:
        logger.warning(f"DDG search failed for '{query}': {e}")
        return []


def _cloud_search(chapter: Chapter, exam: str) -> List[Resource]:
    """On Cloud Run: use Gemini with Google Search Grounding."""
    try:
        import json, google.genai as genai
        from google.genai import types
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )
        prompt = (
            f"For an Indian student preparing for {exam}, find the 3 best FREE online video/reading "
            f"resources for the chapter: '{chapter.title}' (topic: {chapter.description[:200]}). "
            f"Prioritize YouTube lectures by top Indian educators: Physics Wallah (Alakh Pandey/Pankaj Sir), "
            f"Khan Academy India, Vedantu (Shreyas/Abhishek/Vani Ma'am), Unacademy (Namo Kaul), "
            f"Mohit Tyagi (Competishun), Eduniti (Mohit Bhargava), MathonGo (Sameer Bansal), GB Sir, "
            f"Neela Bakore, Biomentors, BYJU'S, NPTEL, Khan Sir (Khan GS), Study IQ, OnlyIAS, VisionIAS, "
            f"Mrunal Patel, Adda247, Rakesh Yadav, Himanshi Singh (CTET), Utkarsh Classes, Magnet Brains, Defence Wallah. "
            f"Return ONLY a JSON array of resources with fields: title, url, platform, teacher, why (1 sentence). "
            f"Each URL must be a real, working YouTube video link you verified via search. "
            f'JSON format: [{{"title":"...","url":"https://...","platform":"youtube","teacher":"...","why":"..."}}]'
        )
        config = types.GenerateContentConfig(
            temperature=0.2,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            system_instruction="You are an academic resource curator for Indian exam aspirants. Return only valid JSON with real URLs from top Indian educator channels. Prefer YouTube links.",
        )
        response = client.models.generate_content(
            model=settings.gemini_model, contents=prompt, config=config,
        )
        text = response.text.strip()
        if text.startswith("```"):
            lines = text.splitlines(); lines = lines[1:]
            while lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        data = json.loads(text)
        out = []
        for item in data[:3]:
            url = item.get("url","")
            if url and url.startswith("http"):
                out.append(Resource(
                    chapter=chapter.title,
                    title=item.get("title", chapter.title)[:140],
                    url=url,
                    platform=item.get("platform","other")[:30],
                    teacher_or_channel=item.get("teacher","")[:80],
                    why=item.get("why","")[:200],
                ))
        return out
    except Exception as e:
        logger.warning(f"Cloud search failed for '{chapter.title}': {e}")
        return []


BAD_DOMAINS = (
    "wikipedia.org","wikibooks.org","pinterest","facebook","instagram",
    "quora.com","scribd.com","coursehero","chegg.com","merriam-webster",
    "dictionary.com","justia.com","usajobs","usa.gov","linkedin.com",
    "amazon.","flipkart","indeed.com","toppr","doubtnut",
)

EDUCATOR_DOMAINS = (
    "youtube.com","youtu.be","khanacademy.org","nptel","vedantu.com",
    "physicswallah","pw.live","unacademy","mohittyagi","competishun",
    "byjus.com","eduniti","mathongo","neelabakore","biomentors",
    "studyiq","study-iq","onlyias","visionias","mrunal",
    "adda247","khangsresearchcentre","khan-sir","magnetbrains",
    "rakeshyadav","deepaktirthyani","utkarsh","defencewallah",
)

EDUCATOR_NAMES = (
    "physics wallah","alakh pandey","pankaj sir","vedantu","khan academy",
    "mohit tyagi","competishun","unacademy","namo kaul","nptel",
    "eduniti","mohit bhargava","vani ma'am","vani maam","gb sir","mathongo",
    "sameer bansal","neela bakore","biomentors","geetendra","geetendra sir",
    "byju","study iq","khan sir","onlyias","vision ias","visionias",
    "mrunal patel","mrunal","adda247","ns sir","vt sir","shreyas sir",
    "abhishek sir","amit sengupta","magnet brains","rakesh yadav",
    "one shot","lecture","tutorial","ncert","pyq","revision",
    "himanshi singh","utkarsh","defence wallah","deepak tirthyani",
    "jaideep sir","gaurav sir","rahul meena","vipan goyal",
)


def _is_educator_resource(url: str, title: str) -> bool:
    url_l = url.lower(); title_l = title.lower()
    for b in BAD_DOMAINS:
        if b in url_l:
            return False
    if any(v in url_l for v in EDUCATOR_DOMAINS):
        return True
    if any(e in title_l for e in EDUCATOR_NAMES):
        return True
    if "youtube.com/results" in url_l or "youtube.com/playlist" in url_l:
        return True
    return False


def _is_relevant(chapter_title: str, url: str, hit_title: str) -> bool:
    ch_words = _word_signature(chapter_title)
    hit_words = _word_signature(hit_title.lower() + " " + url.lower())
    if not ch_words:
        return True
    overlap = ch_words & hit_words
    return len(overlap) >= 1


def find_resources_for_chapter(chapter: Chapter, exam: str) -> List[Resource]:
    """Find 2-4 best free resources for a chapter. NEVER returns empty."""
    resources: List[Resource] = []

    # 1. First: curated database (highest quality, guaranteed real educators)
    curated = _match_curated(chapter.title)
    for c in curated:
        if not any(r.url == c["url"] for r in resources):
            resources.append(Resource(chapter=chapter.title, **c))

    # 2. Try cloud search (if running on GCP with Vertex)
    if settings.is_cloud and settings.google_cloud_project:
        cloud = _cloud_search(chapter, exam)
        for r in cloud:
            if not any(existing.url == r.url for existing in resources):
                resources.append(r)

    # 3. Try DuckDuckGo video search if we still need more
    if len(resources) < 3:
        # Build better search queries with educator hints
        educator_chain = "physics+wallah+OR+vedantu+OR+unacademy+OR+eduniti+OR+mohit+tyagi"
        queries = [
            f'site:youtube.com "{chapter.title}" one shot {exam} {educator_chain}',
            f'{chapter.title} {exam} one shot lecture youtube physics wallah OR khan sir OR study iq',
            f'{chapter.title} class 11 12 JEE NEET youtube lecture',
            f'{chapter.title} {exam} free lecture video',
        ]
        for q in queries:
            if len(resources) >= 4:
                break
            for hit in _ddg_search(q, max_results=3):
                url = hit.get("url","")
                if not url or any(r.url == url for r in resources):
                    continue
                if not _is_educator_resource(url, hit.get("title","")):
                    continue
                if not _is_relevant(chapter.title, url, hit.get("title","")):
                    continue
                resources.append(Resource(
                    chapter=chapter.title,
                    title=hit["title"][:140],
                    url=url,
                    platform=hit["platform"],
                    teacher_or_channel=hit["teacher"],
                    why=hit["why"][:200],
                ))

    # 4. Ultimate fallback: YouTube search page (always works, opens results)
    if len(resources) < 1:
        topic_q = urllib.parse.quote_plus(f"{chapter.title} {exam} one shot")
        resources.append(Resource(
            chapter=chapter.title,
            title=f"YouTube search: {chapter.title} lectures for {exam}",
            url=f"https://www.youtube.com/results?search_query={topic_q}",
            platform="youtube",
            teacher_or_channel="YouTube search",
            why=f"Find the best lecture on {chapter.title} that matches your learning style from top Indian educators.",
        ))

    return resources[:4]


def find_all_resources(chapters: List[Chapter], exam: str) -> List[Resource]:
    """Find resources for all chapters."""
    all_r: List[Resource] = []
    for ch in chapters:
        ch_resources = find_resources_for_chapter(ch, exam)
        all_r.extend(ch_resources)
        logger.info(f"  Found {len(ch_resources)} resources for: {ch.title}")
    return all_r
