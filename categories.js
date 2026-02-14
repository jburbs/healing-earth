// Post category assignments for Healing Earth with Technology
// Each post can belong to multiple categories

const postCategories = {
    // Notes & Asides
    "2021-05-16_000_Healing the Earth": ["notes"],
    "2021-05-17_000_0. About this Newsletter": ["notes"],
    "2021-11-28_000_Thanksgiving break": ["notes"],
    "2021-12-25_000_Merry Christmas!": ["notes"],
    "2022-01-09_000_A pseudo-political diversion": ["notes"],
    "2022-02-13_000_A second pseudo-political diversion": ["notes"],
    "2022-02-15_000_Oops--the missing issue": ["notes"],
    "2022-04-17_000_Another pseudopolitical piece Putin and the Pump": ["notes"],
    "2022-05-08_000_Recommended reading The politics of oil prices from a history professor.": ["notes"],
    "2022-06-20_000_Another pseudopolitical science piece": ["notes"],
    "2022-07-10_000_Renewable electricity and the learning curve": ["notes"],
    "2022-08-08_000_Questions to be answered. With data.": ["notes"],
    "2023-01-01_000_A New Hope": ["notes"],
    "2023-04-13_000_Join me on Notes": ["notes"],
    "2023-07-07_000_Something a little different": ["notes"],
    "2024-01-05_000_A New Year": ["notes"],
    "2024-02-02_000_A pause to catch up": ["notes"],
    "2024-02-03_000_There is a path to healing": ["notes"],
    "2024-10-26_000_Taking a short break (again)": ["notes"],
    "2024-11-09_000_Recovering from a Tuesday hangover": ["notes"],
    "2024-11-24_000_November 17, 2024": ["notes"],
    "2025-01-04_000_Holiday Break(ing)": ["notes"],
    "2025-07-26_000_Going on hiatus": ["notes"],

    // Climate Science
    "2021-05-23_001_Is Global Warming Real": ["climate"],
    "2021-05-30_002_Carbon. Hero or villain": ["climate"],
    "2021-06-06_003_Earth is getting warmer. So what (Part 1)": ["climate"],
    "2021-06-13_004_Where did all that carbon come from": ["climate"],
    "2021-06-20_005_Leading with Data": ["climate", "science"],
    "2021-06-27_006_Is Carbon exonerated by Henry's Law": ["climate"],
    "2021-07-04_007_Earth is getting warmer. So what (Part 2)": ["climate"],
    "2021-07-11_008_What do we know now about Climate Change": ["climate"],
    "2021-08-16_013_Earth is getting warmer. So what (AR6 IPCC WGI Readout)": ["climate", "policy"],
    "2021-08-22_014_Tying up a few loose ends": ["climate"],
    "2021-11-14_026_The science problem with net-zero": ["climate"],
    "2021-12-12_029_The existential threat ignored": ["climate"],
    "2022-01-30_033_The existential threat revisited": ["climate"],
    "2022-02-20_035_Is the California drought due to climate change": ["climate"],
    "2022-02-27_036_Words don't matter (and they do)": ["climate"],
    "2022-07-03_049_Can carbon be stored as topsoil": ["climate", "solutions"],
    "2022-08-14_053_Are trees the best use of land": ["climate", "solutions"],
    "2022-10-03_060_How much tax does 'Nature' owe California": ["climate"],
    "2022-10-10_061_What's the point of 'fighting' climate change": ["climate"],
    "2022-10-16_062_Blindspotting (Part 1)": ["climate"],
    "2022-10-23_063_Blindspotting (Part 2)": ["climate"],
    "2022-10-30_064_Blindspotting (Part 3)": ["climate"],
    "2022-11-06_065_Blindspotting (Part 4)": ["climate"],
    "2022-11-14_066_Blindspotting (Part 5)": ["climate"],
    "2022-11-20_067_Blindspotting (Part 6)": ["climate"],
    "2023-01-09_071_Where is the sink (Part 1)": ["climate"],
    "2023-01-15_072_Where is the sink (Part 2)": ["climate"],
    "2023-02-05_074_Recognizing Personal Bias": ["climate", "science"],
    "2023-02-12_075_Recognizing the bias of models": ["climate", "science"],
    "2023-02-19_076_Returning to the prime directive": ["science"],
    "2023-02-26_077_Experimental Economics": ["policy"],
    "2023-03-05_078_Recap": ["notes"],
    "2023-03-12_079_Climate Control": ["climate", "solutions"],
    "2023-03-26_081_A decarbonization fetish": ["climate"],
    "2023-05-11_088_Why deforestation has no climate effect": ["climate"],
    "2023-09-08_103_COPout...again": ["climate", "policy"],
    "2023-09-21_105_Eco-Anxiety": ["climate", "science"],
    "2023-12-08_115_A different flavor of climate denial": ["climate"],
    "2023-12-16_116_The Engineering Specifications of COP28": ["climate", "policy"],
    "2024-04-23_000_Earth Day + 54 years": ["climate", "notes"],
    "2024-06-08_000_How Environmentalism is Ruining Earth": ["climate", "policy"],
    "2024-06-29_000_The Hidden Danger of Computer Models": ["climate", "science"],
    "2024-09-21_000_Climate Week - Are solutions coming into focus": ["climate", "solutions"],
    "2024-11-16_000_Another year. Another COP. Same ol' same ol'": ["climate", "policy", "notes"],
    "2025-01-25_000_The Leash is Broken": ["climate", "policy"],
    "2025-06-07_000_Environmental Analysis Is Off the Rails": ["climate", "policy", "science"],
    "2024-02-20_000_The meaning of net zero": ["climate"],

    // Solutions & Technology
    "2021-07-18_009_Healing (Part 1). What can we do": ["solutions"],
    "2021-07-25_010_Healing (Part 2). Is decarbonization a solution": ["solutions"],
    "2021-08-01_011_Healing (Part 3). What can the STEM crowd do about it": ["solutions"],
    "2021-08-08_012_Healing (Part 4). A ray of hope.": ["solutions"],
    "2021-08-29_015_Healing (Part 5). Hope Spring(s) eternal": ["solutions"],
    "2021-09-05_016_Healing (Part 6) Oceans of hope": ["solutions"],
    "2021-09-12_017_Healing (Part 7). So...what's it gonna cost me": ["solutions", "policy"],
    "2021-09-19_018_Healing (Part 8). Can water alone be the complete solution": ["solutions"],
    "2021-09-26_019_Healing (Part 9). Avoiding enthusiasm and superstition.": ["solutions"],
    "2021-10-03_020_Healing (Part 10). The nuclear option": ["solutions"],
    "2021-10-10_021_Healing (Part 11). The Only Solution.": ["solutions"],
    "2021-10-17_022_Healing (Part 12). Reducing the only solution to practice": ["solutions"],
    "2021-10-24_023_Evaluating a carbon footprint (Part 1) Boeing vs Tesla": ["solutions"],
    "2021-11-01_024_Evaluating a carbon footprint (Part 2) Crypto vs Credit": ["solutions"],
    "2021-11-07_025_Evaluating a carbon footprint (Part 3) Paper or plastic": ["solutions"],
    "2021-11-21_027_Healing revisited, or Don't we already have a solution": ["solutions"],
    "2021-12-05_028_Healing Earth for the Twitterverse": ["solutions", "notes"],
    "2022-01-16_031_Holoeconomics and Energy (Part 1)": ["solutions", "policy"],
    "2022-01-23_032_Holoeconomics & Energy (Part 2)": ["solutions", "policy"],
    "2022-02-06_034_Holoeconomics & Energy (Part 3)": ["solutions", "policy"],
    "2022-03-06_037_Holoeconomics & Energy (Part 4)": ["solutions", "policy"],
    "2022-03-13_038_Holoeconomics & Energy (Part 4), continued": ["solutions", "policy"],
    "2022-03-20_039_Transitions": ["solutions"],
    "2022-03-27_040_Three simple questions for climate change solutions": ["solutions"],
    "2022-04-03_041_How to Heal Earth for the Visual Learner": ["solutions"],
    "2022-04-24_042_IPCC WG III and reality (Part 1)": ["solutions", "policy"],
    "2022-04-25_042_IPCC WG III and reality (Part 1); Addendum": ["solutions", "policy"],
    "2022-05-01_043_IPCC WG III and reality (Part 2)": ["solutions", "policy"],
    "2022-05-15_044_IPCC WG III and reality (Part 3)": ["solutions", "policy"],
    "2022-05-22_045_First Anniversary Edition": ["solutions", "notes"],
    "2022-06-05_046_Low-cost Desalination and the ARPA-E Summit": ["solutions"],
    "2022-06-12_047_Putin & the Pump revisited": ["notes"],
    "2022-06-26_048_Expanding the case for irrigation": ["solutions"],
    "2022-07-17_050_Solar power at the cost of coal (Part 1)": ["solutions"],
    "2022-07-24_051_Solar power at the cost of coal (Part 2)": ["solutions"],
    "2022-08-01_052_A Trillion trees": ["climate", "solutions"],
    "2022-08-21_054_Does it matter what we plant (Part 1)": ["solutions"],
    "2022-08-28_055_Does it matter what we plant (Part 2)": ["solutions"],
    "2022-09-04_056_Does it matter what we plant (Part 3)": ["solutions"],
    "2022-09-11_057_Another solution (Part 1)": ["solutions"],
    "2022-09-19_058_Another solution (Part 2)": ["solutions"],
    "2022-09-25_059_Another solution (Part 3)": ["solutions"],
    "2022-12-05_068_COP26-to-COP27 Readout": ["climate", "policy"],
    "2022-12-11_069_Why climate innovation is off track": ["solutions", "policy"],
    "2022-12-18_070_Why the news about fusion is bad": ["solutions"],
    "2023-03-19_080_Hydrogen. Atomic No1": ["solutions"],
    "2023-04-02_082_Developing a third solution (Part 1)": ["solutions"],
    "2023-04-09_083_Developing a third solution (Part 2)": ["solutions"],
    "2023-04-16_084_Developing a third solution (Part 3)": ["solutions"],
    "2023-04-23_085_Developing a third solution (Part 4)": ["solutions"],
    "2023-04-30_086_Developing a third solution (part 5)": ["solutions"],
    "2023-05-04_087_Heilmeier and Climate Control": ["solutions", "policy"],
    "2023-06-02_091_Developing a third solution (Part 6)": ["solutions"],
    "2023-06-30_095_Developing a third solution (Part 7)": ["solutions"],
    "2023-07-14_096_Developing a Third Solution (Part 8)": ["solutions"],
    "2023-07-21_097_Developing a Third Solution (Part 9)": ["solutions"],
    "2023-08-03_098_Developing a Third Solution (Part 10)": ["solutions"],
    "2023-08-11_099_Developing a Third Solution (Part 11)": ["solutions"],
    "2023-08-18_100_Reflections": ["notes"],
    "2023-08-25_101_Water in the news": ["solutions"],
    "2023-11-10_111_Are Solar Stills a Solution Yet (Part 1)": ["solutions"],
    "2023-12-01_114_The solution space": ["solutions"],
    "2023-12-21_117_Ending 2023 on an optimistic note": ["solutions"],
    "2024-05-17_000_The Trouble with Science.": ["science"],
    "2024-05-25_000_Engineering, Journalism, and the Circular Firing Squad (Part 1)": ["solutions"],
    "2024-06-01_000_Engineering, Journalism, and the Circular Firing Squad (Part 2)": ["solutions"],
    "2024-06-22_000_Corporate Energy is not the Enemy": ["solutions", "policy"],
    "2024-07-14_000_Engineering vs. Economic Net Zero (Part 1)": ["solutions", "policy"],
    "2024-07-20_000_Engineering vs. Economic Net Zero (Part 2)": ["solutions", "policy"],
    "2024-07-27_000_Engineering vs. Economic Net Zero (Part 3)": ["solutions", "policy"],
    "2024-08-03_000_Engineering and iLUC (Part 1)": ["solutions"],
    "2024-08-10_000_Engineering and iLUC (Part 2)": ["solutions"],
    "2024-08-25_000_Engineering and iLUC (Part 3)": ["solutions"],
    "2024-09-07_000_Doing Something": ["solutions", "ai"],
    "2024-09-14_000_Engineering, Journalism, and the Circular Firing Squad (Part 3)": ["solutions"],
    "2024-09-28_000_Beyond the Limits A Critical Look at Cultured Meat": ["solutions"],
    "2024-10-05_000_Bellwethers": ["solutions", "policy"],
    "2024-10-12_000_The Tragedy of San Onofre": ["solutions"],
    "2024-10-19_000_Water. There is no substitute.": ["solutions"],
    "2024-12-07_000_The Information Paradox": ["ai", "science"],
    "2025-01-11_000_Beyond Good vs. Evil Tradeoffs in Modern Agriculture": ["solutions", "science"],
    "2025-01-18_000_The Scientific Literature is Dead. Now What": ["science", "ai"],
    "2025-02-08_000_Beyond DeSci A Modern Architecture for Scientific Trust": ["ai", "science"],
    "2025-02-22_000_Beyond DeSci Part 2 Starting Small": ["ai", "science"],
    "2025-03-08_000_Beyond DeSci Part 3 From Concept to Code": ["ai", "science"],
    "2025-04-12_000_Rethinking the Energy-Agriculture Nexus": ["solutions"],
    "2025-04-25_000_Making Agrivoltaics Work": ["solutions"],
    "2025-05-24_000_The Information Paradox": ["ai", "science"],
    "2025-05-31_000_Did our Digital Overlord Meet His Match": ["ai", "policy"],
    "2025-06-21_000_Academic Fan-Fic of a Painless Net Zero Future": ["policy", "science"],

    // AI & Technology
    "2023-05-19_089_ChatGPT is a fraud": ["ai"],
    "2023-05-25_090_ChatGPT is a fake. A really talented one!": ["ai"],
    "2023-06-23_094_ChatGPT and Science": ["ai", "science"],
    "2025-06-28_000_AI is turning the corner": ["ai"],

    // Policy & Economics
    "2023-02-26_077_Experimental Economics": ["policy"],
    "2023-06-09_092_John Doerr and me": ["policy"],
    "2023-06-16_093_Seriously, how much money are we talking about": ["policy"],
    "2023-10-12_108_Choosing a frame": ["notes"],
    "2023-10-20_109_A Nobel for data analysis": ["science"],
    "2023-11-12_112_A Holy War": ["notes"],
    "2023-11-22_113_A Thanksgiving Wish": ["notes"],
    "2023-09-14_104_STEM, DEI, and Academic Freedom": ["science"],
    "2023-10-06_107_Academic Integrity Under the Microscope": ["science"],
    "2023-09-29_106_The social cost of privacy": ["policy"],
    "2023-02-19_076_Returning to the prime directive": ["science"],
    "2023-02-12_075_Recognizing the bias of models": ["science"],
    "2023-02-05_074_Recognizing Personal Bias": ["science"],
    "2023-01-22_073_Recognizing the limits of recognition": ["science"],
    "2024-06-15_000_Science in the headlines": ["science"],
    "2024-09-01_000_Science has devolved": ["science"],

    // Science & Methods (non-duplicates)
    "2023-08-31_102_Decarbonization and history": ["climate", "science"],
    "2025-01-11_000_Beyond Good vs. Evil Tradeoffs in Modern Agriculture": ["solutions", "science"],
};

// Series groupings with display info
const seriesData = {
    "Earth is getting warmer": {
        title: "Earth is getting warmer. So what",
        description: "Three-part exploration of global warming and its implications",
        parts: [
            { folder: "2021-06-06_003_Earth is getting warmer. So what (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2021-07-04_007_Earth is getting warmer. So what (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2021-08-16_013_Earth is getting warmer. So what (AR6 IPCC WGI Readout)", partNum: 3, title: "AR6 IPCC WGI Readout" }
        ]
    },
    "Healing": {
        title: "Healing",
        description: "The foundational 12-part series on what we can do about climate change",
        parts: [
            { folder: "2021-07-18_009_Healing (Part 1). What can we do", partNum: 1, title: "Part 1: What can we do" },
            { folder: "2021-07-25_010_Healing (Part 2). Is decarbonization a solution", partNum: 2, title: "Part 2: Is decarbonization a solution" },
            { folder: "2021-08-01_011_Healing (Part 3). What can the STEM crowd do about it", partNum: 3, title: "Part 3: What can the STEM crowd do" },
            { folder: "2021-08-08_012_Healing (Part 4). A ray of hope.", partNum: 4, title: "Part 4: A ray of hope" },
            { folder: "2021-08-29_015_Healing (Part 5). Hope Spring(s) eternal", partNum: 5, title: "Part 5: Hope Springs eternal" },
            { folder: "2021-09-05_016_Healing (Part 6) Oceans of hope", partNum: 6, title: "Part 6: Oceans of hope" },
            { folder: "2021-09-12_017_Healing (Part 7). So...what's it gonna cost me", partNum: 7, title: "Part 7: What's it gonna cost me" },
            { folder: "2021-09-19_018_Healing (Part 8). Can water alone be the complete solution", partNum: 8, title: "Part 8: Water as solution" },
            { folder: "2021-09-26_019_Healing (Part 9). Avoiding enthusiasm and superstition.", partNum: 9, title: "Part 9: Avoiding enthusiasm and superstition" },
            { folder: "2021-10-03_020_Healing (Part 10). The nuclear option", partNum: 10, title: "Part 10: The nuclear option" },
            { folder: "2021-10-10_021_Healing (Part 11). The Only Solution.", partNum: 11, title: "Part 11: The Only Solution" },
            { folder: "2021-10-17_022_Healing (Part 12). Reducing the only solution to practice", partNum: 12, title: "Part 12: Reducing to practice" }
        ]
    },
    "Evaluating a carbon footprint": {
        title: "Evaluating a carbon footprint",
        description: "Three-part analysis of carbon footprints across different domains",
        parts: [
            { folder: "2021-10-24_023_Evaluating a carbon footprint (Part 1) Boeing vs Tesla", partNum: 1, title: "Part 1: Boeing vs Tesla" },
            { folder: "2021-11-01_024_Evaluating a carbon footprint (Part 2) Crypto vs Credit", partNum: 2, title: "Part 2: Crypto vs Credit" },
            { folder: "2021-11-07_025_Evaluating a carbon footprint (Part 3) Paper or plastic", partNum: 3, title: "Part 3: Paper or plastic" }
        ]
    },
    "Holoeconomics & Energy": {
        title: "Holoeconomics & Energy",
        description: "Five-part series on holoeconomics and energy systems",
        parts: [
            { folder: "2022-01-16_031_Holoeconomics and Energy (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2022-01-23_032_Holoeconomics & Energy (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2022-02-06_034_Holoeconomics & Energy (Part 3)", partNum: 3, title: "Part 3" },
            { folder: "2022-03-06_037_Holoeconomics & Energy (Part 4)", partNum: 4, title: "Part 4" },
            { folder: "2022-03-13_038_Holoeconomics & Energy (Part 4), continued", partNum: 5, title: "Part 4 (continued)" }
        ]
    },
    "IPCC WG III and reality": {
        title: "IPCC WG III and reality",
        description: "Four-part analysis of IPCC Working Group III report and climate reality",
        parts: [
            { folder: "2022-04-24_042_IPCC WG III and reality (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2022-04-25_042_IPCC WG III and reality (Part 1); Addendum", partNum: 2, title: "Part 1 Addendum" },
            { folder: "2022-05-01_043_IPCC WG III and reality (Part 2)", partNum: 3, title: "Part 2" },
            { folder: "2022-05-15_044_IPCC WG III and reality (Part 3)", partNum: 4, title: "Part 3" }
        ]
    },
    "Solar power at the cost of coal": {
        title: "Solar power at the cost of coal",
        description: "Two-part exploration of solar energy economics",
        parts: [
            { folder: "2022-07-17_050_Solar power at the cost of coal (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2022-07-24_051_Solar power at the cost of coal (Part 2)", partNum: 2, title: "Part 2" }
        ]
    },
    "Does it matter what we plant": {
        title: "Does it matter what we plant",
        description: "Three-part series on agricultural choices and climate impact",
        parts: [
            { folder: "2022-08-21_054_Does it matter what we plant (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2022-08-28_055_Does it matter what we plant (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2022-09-04_056_Does it matter what we plant (Part 3)", partNum: 3, title: "Part 3" }
        ]
    },
    "Another solution": {
        title: "Another solution",
        description: "Three-part series exploring alternative climate solutions",
        parts: [
            { folder: "2022-09-11_057_Another solution (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2022-09-19_058_Another solution (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2022-09-25_059_Another solution (Part 3)", partNum: 3, title: "Part 3" }
        ]
    },
    "Blindspotting": {
        title: "Blindspotting",
        description: "Six-part series identifying blind spots in climate discussions",
        parts: [
            { folder: "2022-10-16_062_Blindspotting (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2022-10-23_063_Blindspotting (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2022-10-30_064_Blindspotting (Part 3)", partNum: 3, title: "Part 3" },
            { folder: "2022-11-06_065_Blindspotting (Part 4)", partNum: 4, title: "Part 4" },
            { folder: "2022-11-14_066_Blindspotting (Part 5)", partNum: 5, title: "Part 5" },
            { folder: "2022-11-20_067_Blindspotting (Part 6)", partNum: 6, title: "Part 6" }
        ]
    },
    "Where is the sink": {
        title: "Where is the sink",
        description: "Two-part investigation into carbon sinks and removal",
        parts: [
            { folder: "2023-01-09_071_Where is the sink (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2023-01-15_072_Where is the sink (Part 2)", partNum: 2, title: "Part 2" }
        ]
    },
    "Developing a third solution": {
        title: "Developing a third solution",
        description: "Eleven-part series developing alternative approaches to climate solutions",
        parts: [
            { folder: "2023-04-02_082_Developing a third solution (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2023-04-09_083_Developing a third solution (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2023-04-16_084_Developing a third solution (Part 3)", partNum: 3, title: "Part 3" },
            { folder: "2023-04-23_085_Developing a third solution (Part 4)", partNum: 4, title: "Part 4" },
            { folder: "2023-04-30_086_Developing a third solution (part 5)", partNum: 5, title: "Part 5" },
            { folder: "2023-06-02_091_Developing a third solution (Part 6)", partNum: 6, title: "Part 6" },
            { folder: "2023-06-30_095_Developing a third solution (Part 7)", partNum: 7, title: "Part 7" },
            { folder: "2023-07-14_096_Developing a Third Solution (Part 8)", partNum: 8, title: "Part 8" },
            { folder: "2023-07-21_097_Developing a Third Solution (Part 9)", partNum: 9, title: "Part 9" },
            { folder: "2023-08-03_098_Developing a Third Solution (Part 10)", partNum: 10, title: "Part 10" },
            { folder: "2023-08-11_099_Developing a Third Solution (Part 11)", partNum: 11, title: "Part 11" }
        ]
    },
    "ChatGPT": {
        title: "ChatGPT",
        description: "Three-part analysis of ChatGPT and its implications",
        parts: [
            { folder: "2023-05-19_089_ChatGPT is a fraud", partNum: 1, title: "ChatGPT is a fraud" },
            { folder: "2023-05-25_090_ChatGPT is a fake. A really talented one!", partNum: 2, title: "ChatGPT is a fake" },
            { folder: "2023-06-23_094_ChatGPT and Science", partNum: 3, title: "ChatGPT and Science" }
        ]
    },
    "Engineering, Journalism, and the Circular Firing Squad": {
        title: "Engineering, Journalism, and the Circular Firing Squad",
        description: "Three-part exploration of engineering, journalism, and mutual criticism",
        parts: [
            { folder: "2024-05-25_000_Engineering, Journalism, and the Circular Firing Squad (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2024-06-01_000_Engineering, Journalism, and the Circular Firing Squad (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2024-09-14_000_Engineering, Journalism, and the Circular Firing Squad (Part 3)", partNum: 3, title: "Part 3" }
        ]
    },
    "Engineering vs. Economic Net Zero": {
        title: "Engineering vs. Economic Net Zero",
        description: "Three-part comparison of engineering and economic approaches to net zero",
        parts: [
            { folder: "2024-07-14_000_Engineering vs. Economic Net Zero (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2024-07-20_000_Engineering vs. Economic Net Zero (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2024-07-27_000_Engineering vs. Economic Net Zero (Part 3)", partNum: 3, title: "Part 3" }
        ]
    },
    "Engineering and iLUC": {
        title: "Engineering and iLUC",
        description: "Three-part series on indirect land use change and engineering solutions",
        parts: [
            { folder: "2024-08-03_000_Engineering and iLUC (Part 1)", partNum: 1, title: "Part 1" },
            { folder: "2024-08-10_000_Engineering and iLUC (Part 2)", partNum: 2, title: "Part 2" },
            { folder: "2024-08-25_000_Engineering and iLUC (Part 3)", partNum: 3, title: "Part 3" }
        ]
    },
    "Beyond DeSci": {
        title: "Beyond DeSci",
        description: "Three-part series on decentralized science and scientific trust",
        parts: [
            { folder: "2025-02-08_000_Beyond DeSci A Modern Architecture for Scientific Trust", partNum: 1, title: "A Modern Architecture for Scientific Trust" },
            { folder: "2025-02-22_000_Beyond DeSci Part 2 Starting Small", partNum: 2, title: "Part 2: Starting Small" },
            { folder: "2025-03-08_000_Beyond DeSci Part 3 From Concept to Code", partNum: 3, title: "Part 3: From Concept to Code" }
        ]
    },
    "The Evolution of Elon Musk": {
        title: "The Evolution of Elon Musk",
        description: "Four-part series on Elon Musk's evolution and impact",
        parts: [
            { folder: "2025-03-15_000_The Evolution of Elon Musk, Part 1.", partNum: 1, title: "Part 1" },
            { folder: "2025-03-23_000_The Evolution of Elon Musk, Part 2", partNum: 2, title: "Part 2" },
            { folder: "2025-03-29_000_The Evolution of Elon Musk, Part 3", partNum: 3, title: "Part 3" },
            { folder: "2025-05-31_000_Did our Digital Overlord Meet His Match", partNum: 4, title: "Did our Digital Overlord Meet His Match" }
        ]
    },
    "Agrivoltaics": {
        title: "Agrivoltaics",
        description: "Two-part series on combining agriculture and energy generation",
        parts: [
            { folder: "2025-04-12_000_Rethinking the Energy-Agriculture Nexus", partNum: 1, title: "Rethinking the Energy-Agriculture Nexus" },
            { folder: "2025-04-25_000_Making Agrivoltaics Work", partNum: 2, title: "Making Agrivoltaics Work" }
        ]
    }
};

// Export for use in other modules
if (typeof module !== "undefined" && module.exports) {
    module.exports = { postCategories, seriesData };
}
