"use strict";
/* Shared helpers for every page: DOM, number formats, theme, menu, tooltip and the small SVG charts. No libraries. */
(function () {
  var MINUS = "−";
  var SVGNS = "http://www.w3.org/2000/svg";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var PAGES = [["/today", "navToday"], ["/explore", "navExplore"], ["/report", "navWeekly"], ["/method", "navMethod"], ["/help", "navHelp"]];
  var I18N = {
    en: {
      language: "English", chooseLanguage: "Choose language", navToday: "Today", navExplore: "Explore", navWeekly: "Weekly report", navMethod: "How it works", navHelp: "Help", sourceCode: "Source code",
      theme: "Theme", sourceNote: "Source: Statistics Department, Central Bank of Sri Lanka, Daily Price Reports. The Central Bank does not endorse this project or its findings. Estimates are statistical, not advice.",
      welcomeBadge: "Independent student project", welcomeEyebrow: "A clearer view of everyday food prices", welcomeTitle: "See how Dambulla price changes may reach Colombo markets", welcomeLede: "Price Signal turns daily price reports into a simple, careful guide for canteens, restaurants, shops and other small food buyers.", welcomeOpen: "Open today's price guide", welcomeLearn: "Learn how it works", welcomeChecking: "Checking the latest report...",
      notOfficial: "Not an official government service.", notOfficialBody: "The emblem identifies the country only. This independent student project is not endorsed by the Government of Sri Lanka, the Central Bank of Sri Lanka or its Statistics Department.",
      officialSource: "Official source data", officialSourceValue: "CBSL Daily Price Reports", practicalUse: "Made for practical use", practicalUseValue: "Small food buyers in Colombo", shortView: "Short-term view", shortViewValue: "The following 3 report days", safetyFirst: "Safety first", safetyFirstValue: "No estimate when data are not ready",
      helps: "What the website helps you do", reportToCheck: "From a daily report to a useful price check", control: "You stay in control. The website explains what the data suggest and where the uncertainty is; it never tells you to buy, wait or sell.", chooseMarket: "Choose your market", chooseMarketBody: "Compare Dambulla wholesale prices with Pettah or Narahenpita.", likelyDirection: "Read the expected direction", likelyDirectionBody: "See whether the current estimate points upward or downward over the following three report days.", checkUncertainty: "Check the uncertainty", checkUncertaintyBody: "Use the possible range and signal strength before deciding how much confidence to place in the estimate.",
      severalViews: "One website, several views", startSimple: "Start simple, then explore the evidence", viewsBody: "Today gives you the quick view. Explore shows price history. Weekly Report compares recent weeks. How it works explains how the estimates were checked.", goToday: "Go to today's guide", todayDesc: "Current estimates and data checks", exploreDesc: "Past prices and market gaps", weeklyDesc: "This week compared with last week", methodDesc: "Testing, limits and evidence", infoNotAdvice: "Use it as information, not advice", disclaimer: "Price Signal uses Daily Price Reports published by the Statistics Department, Central Bank of Sri Lanka. Estimates are statistical and uncertain. The Central Bank bears no responsibility for and does not endorse this project or its findings.",
      latestReady: "Latest report: {date} - information ready", estimatesHidden: "Today's estimates are currently hidden: {reason}", latestFailed: "The latest report could not be checked just now.",
      todayEyebrow: "Colombo food price guide - following 3 report days", checkingReport: "Checking the latest report", compareEstimates: "Compare the estimates", expectedChange: "Expected change and uncertainty", eachPoint: "Each point represents one item", strongerSignal: "Stronger signal", earlySignal: "Early signal", higherUncertain: "Higher on chart = more uncertainty", checkFirst: "What to check first", strongestToday: "Strongest signals today", watchFoot: "Items with stronger signals appear first. This is information, not buying advice.",
      availableEstimates: "Available estimates", availableValue: "{ok} of {total}", unavailableNote: "{count} items do not have enough reliable information today", clearerEstimates: "Clearer estimates", clearerNote: "These have the strongest support from the recent price pattern", directionOutlook: "Expected direction", directionValue: "Upward: {up} · Downward: {down}", directionNote: "Current estimates grouped by direction; this is not buying advice", averageRange: "Average range width", averageRangeValue: "{value} points", averageRangeNote: "Distance from each range's low end to high end; smaller is more precise",
      estimateHeadline: "{ok} of {total} items have an estimate", noClearToday: "No item has a clear signal today", basedOn: "Based on the CBSL Daily Price Report of {date}. Each estimate compares Dambulla wholesale with a Colombo price.", dataOld: "The data are too old", sourceUnavailable: "The source could not be checked", newerUnread: "A newer report is not read yet", priceData: "Price data {date}", sourceVerified: "Source verified", sourceWithheld: "Source withheld", workingAgeOne: "1 working day old", workingAgeMany: "{count} working days old", observedHistory: "Observed history", syntheticHistory: "Synthetic history",
      estimatesHiddenShort: "Estimates are currently hidden", shown: "{count} shown", noSignals: "No signals are available", uncertainty: "uncertainty", noMap: "No active estimates are available for the map.",
      allChecks: "All checks passed", checksHidden: "Estimates are hidden", sourceWebsite: "Source website", latestChecked: "Latest listing checked", needsAttention: "Needs attention", dataFreshness: "Data freshness", allowedDays: "{age} of {max} allowed working days", itemsChecked: "Items checked", itemsMarket: "{count} items for this market", priceHistory: "Price history", observedData: "Observed source data", demoData: "Made-up demonstration data", websiteUpdated: "Website updated", unknown: "Unknown"
    },
    si: {
      language: "සිංහල", chooseLanguage: "භාෂාව තෝරන්න", navToday: "අද", navExplore: "ගවේෂණය", navWeekly: "සතිපතා වාර්තාව", navMethod: "ක්‍රියා කරන ආකාරය", navHelp: "උදව්", sourceCode: "මූලාශ්‍ර කේතය",
      theme: "තේමාව", sourceNote: "මූලාශ්‍රය: ශ්‍රී ලංකා මහ බැංකුවේ සංඛ්‍යාලේඛන දෙපාර්තමේන්තුවේ දෛනික මිල වාර්තා. මහ බැංකුව මෙම ව්‍යාපෘතිය හෝ එහි ප්‍රතිඵල අනුමත නොකරයි. මෙය සංඛ්‍යානමය තොරතුරක් මිස උපදෙස් නොවේ.",
      welcomeBadge: "ස්වාධීන ශිෂ්‍ය ව්‍යාපෘතිය", welcomeEyebrow: "දෛනික ආහාර මිල ගැන වඩා පැහැදිලි දැක්මක්", welcomeTitle: "දඹුල්ල මිල වෙනස්වීම් කොළඹ වෙළඳපොළට පැමිණිය හැකි ආකාරය බලන්න", welcomeLede: "Price Signal දෛනික මිල වාර්තා ආපනශාලා, වෙළඳසැල් සහ අනෙකුත් කුඩා ආහාර ගැනුම්කරුවන් සඳහා සරල හා සැලකිලිමත් මාර්ගෝපදේශයකට පරිවර්තනය කරයි.", welcomeOpen: "අද මිල මාර්ගෝපදේශය විවෘත කරන්න", welcomeLearn: "ක්‍රියා කරන ආකාරය බලන්න", welcomeChecking: "නවතම වාර්තාව පරීක්ෂා කරමින්...",
      notOfficial: "මෙය නිල රාජ්‍ය සේවාවක් නොවේ.", notOfficialBody: "ලාංඡනය රට හඳුනාගැනීම සඳහා පමණි. මෙම ස්වාධීන ශිෂ්‍ය ව්‍යාපෘතිය ශ්‍රී ලංකා රජය, ශ්‍රී ලංකා මහ බැංකුව හෝ එහි සංඛ්‍යාලේඛන දෙපාර්තමේන්තුව විසින් අනුමත කර නැත.",
      officialSource: "නිල දත්ත මූලාශ්‍රය", officialSourceValue: "CBSL දෛනික මිල වාර්තා", practicalUse: "ප්‍රායෝගික භාවිතයට", practicalUseValue: "කොළඹ කුඩා ආහාර ගැනුම්කරුවන්", shortView: "කෙටි කාලීන දැක්ම", shortViewValue: "ඊළඟ වාර්තා දින 3", safetyFirst: "ආරක්ෂාව පළමුව", safetyFirstValue: "දත්ත සූදානම් නැත්නම් ඇස්තමේන්තුවක් නැත",
      helps: "මෙම වෙබ් අඩවිය ඔබට උපකාර කරන දේ", reportToCheck: "දෛනික වාර්තාවකින් ප්‍රයෝජනවත් මිල පරීක්ෂාවකට", control: "තීරණය ඔබ සතුය. දත්ත පෙන්වන දේ සහ අවිනිශ්චිතතාව මෙහි පැහැදිලි කරයි; මිලදී ගන්න, රැඳී සිටින්න හෝ විකුණන්නැයි මෙය නොකියයි.", chooseMarket: "ඔබේ වෙළඳපොළ තෝරන්න", chooseMarketBody: "දඹුල්ල තොග මිල පිටකොටුව හෝ නාරාහේන්පිට මිල සමඟ සසඳන්න.", likelyDirection: "අපේක්ෂිත දිශාව බලන්න", likelyDirectionBody: "ඊළඟ වාර්තා දින තුන තුළ ඇස්තමේන්තුව ඉහළටද පහළටද යොමු වන්නේද බලන්න.", checkUncertainty: "අවිනිශ්චිතතාව පරීක්ෂා කරන්න", checkUncertaintyBody: "ඇස්තමේන්තුව පිළිබඳ විශ්වාසය තීරණය කිරීමට පෙර හැකි පරාසය සහ සංඥා ශක්තිය බලන්න.",
      severalViews: "එක් වෙබ් අඩවියක්, දැක්ම කිහිපයක්", startSimple: "සරලව ආරම්භ කර සාක්ෂි ගවේෂණය කරන්න", viewsBody: "අද පිටුව ඉක්මන් සාරාංශය ලබාදෙයි. ගවේෂණය මිල ඉතිහාසය පෙන්වයි. සතිපතා වාර්තාව සති සසඳයි. ක්‍රියා කරන ආකාරය පිටුව ඇස්තමේන්තු පරීක්ෂා කළ ආකාරය පැහැදිලි කරයි.", goToday: "අද මාර්ගෝපදේශයට යන්න", todayDesc: "වත්මන් ඇස්තමේන්තු සහ දත්ත පරීක්ෂා", exploreDesc: "පසුගිය මිල සහ වෙළඳපොළ පරතර", weeklyDesc: "මෙම සතිය පසුගිය සතිය සමඟ", methodDesc: "පරීක්ෂණ, සීමා සහ සාක්ෂි", infoNotAdvice: "උපදෙස් ලෙස නොව තොරතුරු ලෙස භාවිත කරන්න", disclaimer: "Price Signal ශ්‍රී ලංකා මහ බැංකුවේ සංඛ්‍යාලේඛන දෙපාර්තමේන්තුව ප්‍රකාශ කරන දෛනික මිල වාර්තා භාවිත කරයි. ඇස්තමේන්තු සංඛ්‍යානමය සහ අවිනිශ්චිතය. මහ බැංකුව මෙම ව්‍යාපෘතිය හෝ එහි ප්‍රතිඵල සඳහා වගකීම භාර නොගන්නා අතර ඒවා අනුමත නොකරයි.",
      latestReady: "නවතම වාර්තාව: {date} - තොරතුරු සූදානම්", estimatesHidden: "අද ඇස්තමේන්තු සඟවා ඇත: {reason}", latestFailed: "නවතම වාර්තාව දැන් පරීක්ෂා කළ නොහැක.",
      todayEyebrow: "කොළඹ ආහාර මිල මාර්ගෝපදේශය - ඊළඟ වාර්තා දින 3", checkingReport: "නවතම වාර්තාව පරීක්ෂා කරමින්", compareEstimates: "ඇස්තමේන්තු සසඳන්න", expectedChange: "අපේක්ෂිත වෙනස සහ අවිනිශ්චිතතාව", eachPoint: "සෑම ලක්ෂ්‍යයක්ම භාණ්ඩයක් නිරූපණය කරයි", strongerSignal: "වඩා පැහැදිලි සංඥාව", earlySignal: "ආරම්භක සංඥාව", higherUncertain: "ඉහළ ලක්ෂ්‍ය = වැඩි අවිනිශ්චිතතාව", checkFirst: "පළමුව බලන්න", strongestToday: "අද වඩා පැහැදිලි සංඥා", watchFoot: "වඩා පැහැදිලි සංඥා පළමුව පෙන්වයි. මෙය තොරතුරක් මිස මිලදී ගැනීමේ උපදෙස් නොවේ.",
      availableEstimates: "ලබාගත හැකි ඇස්තමේන්තු", availableValue: "{total} න් {ok}", unavailableNote: "භාණ්ඩ {count}කට අද ප්‍රමාණවත් විශ්වාසදායක තොරතුරු නැත", clearerEstimates: "වඩා පැහැදිලි ඇස්තමේන්තු", clearerNote: "මෑත මිල රටාවෙන් වැඩිම සහාය ඇති ඇස්තමේන්තු", directionOutlook: "අපේක්ෂිත දිශාව", directionValue: "ඉහළට: {up} · පහළට: {down}", directionNote: "වත්මන් ඇස්තමේන්තු දිශාව අනුව කාණ්ඩ කර ඇත; මෙය මිලදී ගැනීමේ උපදෙස් නොවේ", averageRange: "සාමාන්‍ය පරාස පළල", averageRangeValue: "ලකුණු {value}", averageRangeNote: "අඩු සහ ඉහළ සීමා අතර දුර; කුඩා අගයක් වඩා නිරවද්‍යයි",
      estimateHeadline: "භාණ්ඩ {total} න් {ok}කට ඇස්තමේන්තුවක් ඇත", noClearToday: "අද කිසිදු භාණ්ඩයකට පැහැදිලි සංඥාවක් නැත", basedOn: "{date} දින CBSL දෛනික මිල වාර්තාව මත පදනම් වේ. සෑම ඇස්තමේන්තුවක්ම දඹුල්ල තොග මිල කොළඹ මිලක් සමඟ සසඳයි.", dataOld: "දත්ත පැරණියි", sourceUnavailable: "මූලාශ්‍රය පරීක්ෂා කළ නොහැක", newerUnread: "නව වාර්තාවක් තවම කියවා නැත", priceData: "මිල දත්ත {date}", sourceVerified: "මූලාශ්‍රය තහවුරු කර ඇත", sourceWithheld: "මූලාශ්‍රය රඳවා ඇත", workingAgeOne: "වැඩ කරන දින 1ක් පැරණියි", workingAgeMany: "වැඩ කරන දින {count}ක් පැරණියි", observedHistory: "නිරීක්ෂිත මිල ඉතිහාසය", syntheticHistory: "අත්හදා බැලීමේ දත්ත",
      estimatesHiddenShort: "ඇස්තමේන්තු දැනට සඟවා ඇත", shown: "{count}ක් පෙන්වයි", noSignals: "සංඥා නොමැත", uncertainty: "අවිනිශ්චිතතාව", noMap: "සිතියම සඳහා සක්‍රීය ඇස්තමේන්තු නොමැත.", allChecks: "සියලු පරීක්ෂා සාර්ථකයි", checksHidden: "ඇස්තමේන්තු සඟවා ඇත", sourceWebsite: "මූලාශ්‍ර වෙබ් අඩවිය", latestChecked: "නවතම ලැයිස්තුව පරීක්ෂා කර ඇත", needsAttention: "අවධානය අවශ්‍යයි", dataFreshness: "දත්ත නවතාව", allowedDays: "අවසර ලත් වැඩ දින {max} න් {age}", itemsChecked: "පරීක්ෂා කළ භාණ්ඩ", itemsMarket: "මෙම වෙළඳපොළ සඳහා භාණ්ඩ {count}", priceHistory: "මිල ඉතිහාසය", observedData: "නිරීක්ෂිත මූලාශ්‍ර දත්ත", demoData: "අත්හදා බැලීමේ දත්ත", websiteUpdated: "වෙබ් අඩවිය යාවත්කාලීන කළේ", unknown: "නොදනී"
    },
    ta: {
      language: "தமிழ்", chooseLanguage: "மொழியைத் தேர்ந்தெடுக்கவும்", navToday: "இன்று", navExplore: "ஆராய்வு", navWeekly: "வாராந்திர அறிக்கை", navMethod: "செயல்படும் விதம்", navHelp: "உதவி", sourceCode: "மூலக் குறியீடு",
      theme: "தோற்றம்", sourceNote: "மூலம்: இலங்கை மத்திய வங்கியின் புள்ளிவிபரத் துறையின் தினசரி விலை அறிக்கைகள். மத்திய வங்கி இந்தத் திட்டத்தையோ அதன் முடிவுகளையோ ஆதரிக்கவில்லை. இவை புள்ளிவிபரத் தகவல்கள்; ஆலோசனை அல்ல.",
      welcomeBadge: "சுயாதீன மாணவர் திட்டம்", welcomeEyebrow: "அன்றாட உணவு விலைகளின் தெளிவான பார்வை", welcomeTitle: "தம்புள்ளை விலை மாற்றங்கள் கொழும்புச் சந்தைகளை எவ்வாறு சென்றடையலாம் என்பதைப் பாருங்கள்", welcomeLede: "Price Signal தினசரி விலை அறிக்கைகளை உணவகங்கள், கடைகள் மற்றும் பிற சிறிய உணவு வாங்குபவர்களுக்கான எளிய, கவனமான வழிகாட்டியாக மாற்றுகிறது.", welcomeOpen: "இன்றைய விலை வழிகாட்டியைத் திறக்கவும்", welcomeLearn: "இது எவ்வாறு செயல்படுகிறது", welcomeChecking: "புதிய அறிக்கை சரிபார்க்கப்படுகிறது...",
      notOfficial: "இது அதிகாரப்பூர்வ அரச சேவை அல்ல.", notOfficialBody: "சின்னம் நாட்டை அடையாளப்படுத்துவதற்காக மட்டுமே பயன்படுத்தப்படுகிறது. இந்த சுயாதீன மாணவர் திட்டம் இலங்கை அரசு, இலங்கை மத்திய வங்கி அல்லது அதன் புள்ளிவிபரத் துறையால் ஆதரிக்கப்படவில்லை.",
      officialSource: "அதிகாரப்பூர்வ தரவு மூலம்", officialSourceValue: "CBSL தினசரி விலை அறிக்கைகள்", practicalUse: "நடைமுறை பயன்பாட்டிற்காக", practicalUseValue: "கொழும்பின் சிறிய உணவு வாங்குபவர்கள்", shortView: "குறுகிய காலப் பார்வை", shortViewValue: "அடுத்த 3 அறிக்கை நாட்கள்", safetyFirst: "பாதுகாப்பு முதலில்", safetyFirstValue: "தரவு தயாராக இல்லையெனில் மதிப்பீடு இல்லை",
      helps: "இந்த இணையதளம் உதவும் விதம்", reportToCheck: "தினசரி அறிக்கையிலிருந்து பயனுள்ள விலைச் சரிபார்ப்பு வரை", control: "முடிவு உங்களுடையது. தரவு சுட்டும் விடயங்களையும் நிச்சயமின்மையையும் இணையதளம் விளக்குகிறது; வாங்க, காத்திருக்க அல்லது விற்கும்படி கூறாது.", chooseMarket: "உங்கள் சந்தையைத் தேர்ந்தெடுக்கவும்", chooseMarketBody: "தம்புள்ளை மொத்த விலைகளை புறக்கோட்டை அல்லது நாரஹேன்பிட்ட விலைகளுடன் ஒப்பிடுங்கள்.", likelyDirection: "எதிர்பார்க்கப்படும் திசையைப் பாருங்கள்", likelyDirectionBody: "அடுத்த மூன்று அறிக்கை நாட்களில் தற்போதைய மதிப்பீடு மேல்நோக்கியதா கீழ்நோக்கியதா என்பதைப் பாருங்கள்.", checkUncertainty: "நிச்சயமின்மையைச் சரிபார்க்கவும்", checkUncertaintyBody: "மதிப்பீட்டில் எவ்வளவு நம்பிக்கை வைப்பது என்பதைத் தீர்மானிப்பதற்கு முன் சாத்தியமான வரம்பையும் சமிக்ஞையின் வலிமையையும் பாருங்கள்.",
      severalViews: "ஒரே இணையதளம், பல பார்வைகள்", startSimple: "எளிமையாகத் தொடங்கி ஆதாரத்தை ஆராயுங்கள்", viewsBody: "இன்று விரைவான பார்வையை வழங்குகிறது. ஆராய்வு விலை வரலாற்றைக் காட்டுகிறது. வாராந்திர அறிக்கை அண்மைய வாரங்களை ஒப்பிடுகிறது. செயல்படும் விதம் மதிப்பீடுகள் எவ்வாறு சரிபார்க்கப்பட்டன என்பதை விளக்குகிறது.", goToday: "இன்றைய வழிகாட்டிக்குச் செல்லவும்", todayDesc: "தற்போதைய மதிப்பீடுகள் மற்றும் தரவு சோதனைகள்", exploreDesc: "முந்தைய விலைகள் மற்றும் சந்தை இடைவெளிகள்", weeklyDesc: "இந்த வாரம் கடந்த வாரத்துடன்", methodDesc: "சோதனை, வரம்புகள் மற்றும் ஆதாரம்", infoNotAdvice: "ஆலோசனையாக அல்ல, தகவலாகப் பயன்படுத்தவும்", disclaimer: "Price Signal இலங்கை மத்திய வங்கியின் புள்ளிவிபரத் துறை வெளியிடும் தினசரி விலை அறிக்கைகளைப் பயன்படுத்துகிறது. மதிப்பீடுகள் புள்ளிவிபரமானவை மற்றும் நிச்சயமற்றவை. இந்தத் திட்டத்திற்கோ அதன் முடிவுகளுக்கோ மத்திய வங்கி பொறுப்பேற்காது அல்லது ஆதரிக்காது.",
      latestReady: "புதிய அறிக்கை: {date} - தகவல் தயார்", estimatesHidden: "இன்றைய மதிப்பீடுகள் மறைக்கப்பட்டுள்ளன: {reason}", latestFailed: "புதிய அறிக்கையை இப்போது சரிபார்க்க முடியவில்லை.",
      todayEyebrow: "கொழும்பு உணவு விலை வழிகாட்டி - அடுத்த 3 அறிக்கை நாட்கள்", checkingReport: "புதிய அறிக்கை சரிபார்க்கப்படுகிறது", compareEstimates: "மதிப்பீடுகளை ஒப்பிடுங்கள்", expectedChange: "எதிர்பார்க்கப்படும் மாற்றமும் நிச்சயமின்மையும்", eachPoint: "ஒவ்வொரு புள்ளியும் ஒரு பொருளைக் குறிக்கிறது", strongerSignal: "தெளிவான சமிக்ஞை", earlySignal: "ஆரம்ப சமிக்ஞை", higherUncertain: "மேலுள்ள புள்ளி = அதிக நிச்சயமின்மை", checkFirst: "முதலில் பார்க்க வேண்டியது", strongestToday: "இன்றைய தெளிவான சமிக்ஞைகள்", watchFoot: "தெளிவான சமிக்ஞைகள் முதலில் காட்டப்படுகின்றன. இது தகவல் மட்டுமே; வாங்கும் ஆலோசனை அல்ல.",
      availableEstimates: "கிடைக்கும் மதிப்பீடுகள்", availableValue: "{total} இல் {ok}", unavailableNote: "{count} பொருட்களுக்கு இன்று போதுமான நம்பகமான தகவல் இல்லை", clearerEstimates: "தெளிவான மதிப்பீடுகள்", clearerNote: "அண்மைய விலை முறையின் வலுவான ஆதரவு உள்ளவை", directionOutlook: "எதிர்பார்க்கப்படும் திசை", directionValue: "மேல்நோக்கி: {up} · கீழ்நோக்கி: {down}", directionNote: "தற்போதைய மதிப்பீடுகள் திசைப்படி தொகுக்கப்பட்டுள்ளன; இது வாங்கும் ஆலோசனை அல்ல", averageRange: "சராசரி வரம்பு அகலம்", averageRangeValue: "{value} புள்ளிகள்", averageRangeNote: "குறைந்த மற்றும் அதிக எல்லைகளுக்கிடையிலான தூரம்; குறைவானது துல்லியமானது",
      estimateHeadline: "{total} பொருட்களில் {ok}க்கு மதிப்பீடு உள்ளது", noClearToday: "இன்று எந்தப் பொருளுக்கும் தெளிவான சமிக்ஞை இல்லை", basedOn: "{date} தேதியிட்ட CBSL தினசரி விலை அறிக்கையை அடிப்படையாகக் கொண்டது. ஒவ்வொரு மதிப்பீடும் தம்புள்ளை மொத்த விலையை கொழும்பு விலையுடன் ஒப்பிடுகிறது.", dataOld: "தரவு பழையது", sourceUnavailable: "மூலத்தைச் சரிபார்க்க முடியவில்லை", newerUnread: "புதிய அறிக்கை இன்னும் வாசிக்கப்படவில்லை", priceData: "விலைத் தரவு {date}", sourceVerified: "மூலம் சரிபார்க்கப்பட்டது", sourceWithheld: "மூலம் தடுக்கப்பட்டுள்ளது", workingAgeOne: "1 வேலை நாள் பழையது", workingAgeMany: "{count} வேலை நாட்கள் பழையது", observedHistory: "கவனிக்கப்பட்ட விலை வரலாறு", syntheticHistory: "சோதனைத் தரவு",
      estimatesHiddenShort: "மதிப்பீடுகள் தற்போது மறைக்கப்பட்டுள்ளன", shown: "{count} காட்டப்படுகிறது", noSignals: "சமிக்ஞைகள் இல்லை", uncertainty: "நிச்சயமின்மை", noMap: "வரைபடத்திற்கான செயலில் உள்ள மதிப்பீடுகள் இல்லை.", allChecks: "அனைத்து சோதனைகளும் நிறைவேற்றப்பட்டன", checksHidden: "மதிப்பீடுகள் மறைக்கப்பட்டுள்ளன", sourceWebsite: "மூல இணையதளம்", latestChecked: "புதிய பட்டியல் சரிபார்க்கப்பட்டது", needsAttention: "கவனம் தேவை", dataFreshness: "தரவு புதுமை", allowedDays: "அனுமதிக்கப்பட்ட {max} வேலை நாட்களில் {age}", itemsChecked: "சரிபார்க்கப்பட்ட பொருட்கள்", itemsMarket: "இந்தச் சந்தையில் {count} பொருட்கள்", priceHistory: "விலை வரலாறு", observedData: "கவனிக்கப்பட்ட மூலத் தரவு", demoData: "சோதனைத் தரவு", websiteUpdated: "இணையதளம் புதுப்பிக்கப்பட்டது", unknown: "தெரியவில்லை"
    }
  };
  var PS = window.PS = {};

  function savedLanguage() {
    try { return localStorage.getItem("ps-language") || "en"; } catch (e) { return "en"; }
  }
  PS.lang = I18N[savedLanguage()] ? savedLanguage() : "en";
  PS.t = function (key, vars) {
    var text = (I18N[PS.lang] && I18N[PS.lang][key]) || I18N.en[key] || key;
    Object.keys(vars || {}).forEach(function (name) { text = text.replaceAll("{" + name + "}", vars[name]); });
    return text;
  };
  PS.applyTranslations = function (root) {
    (root || document).querySelectorAll("[data-i18n]").forEach(function (node) { node.textContent = PS.t(node.getAttribute("data-i18n")); });
    document.documentElement.lang = PS.lang;
  };
  PS.initLanguage = function () {
    var select = PS.$("language");
    if (!select) {
      var theme = PS.$("theme");
      if (!theme || !theme.parentNode) return;
      var label = PS.el("label", "language-control");
      label.appendChild(PS.el("span", "sr", PS.t("chooseLanguage")));
      select = PS.el("select"); select.id = "language"; select.setAttribute("aria-label", PS.t("chooseLanguage"));
      [["en", "English"], ["si", "සිංහල"], ["ta", "தமிழ்"]].forEach(function (x) { var o = PS.el("option", null, x[1]); o.value = x[0]; select.appendChild(o); });
      label.appendChild(select); theme.parentNode.insertBefore(label, theme);
    }
    select.value = PS.lang;
    select.setAttribute("aria-label", PS.t("chooseLanguage"));
    select.addEventListener("change", function () {
      try { localStorage.setItem("ps-language", select.value); } catch (e) { /* continue with this page */ }
      location.reload();
    });
    PS.applyTranslations();
  };

  PS.MINUS = MINUS;
  PS.NAMES = { "retail Pettah": "Retail, Pettah", "wholesale Pettah": "Wholesale, Pettah", "retail Narahenpita": "Retail, Narahenpita" };

  PS.el = function (tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  };
  PS.s = function (tag, attrs, text) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  };
  PS.$ = function (id) { return document.getElementById(id); };
  PS.signed = function (v, d) {
    if (v == null || isNaN(v)) return "";
    var s = Math.abs(v).toFixed(d == null ? 1 : d);
    return (v < 0 ? MINUS : v > 0 ? "+" : "") + s;
  };
  PS.arrow = function (v) { return v == null ? "" : v < 0 ? "▼ " : v > 0 ? "▲ " : ""; };
  PS.rs = function (v) { return v == null ? "" : "Rs " + Math.round(v).toLocaleString("en-US"); };
  PS.date = function (iso, year) {
    var p = iso.split("-");
    return parseInt(p[2], 10) + " " + MONTHS[parseInt(p[1], 10) - 1] + (year ? " " + p[0] : "");
  };
  PS.get = function (url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + " returned " + r.status);
      return r.json();
    });
  };

  // ---------- theme ----------
  function applyTheme(t) { if (t) document.documentElement.setAttribute("data-theme", t); else document.documentElement.removeAttribute("data-theme"); }
  try { applyTheme(localStorage.getItem("ps-theme")); } catch (e) { /* storage blocked: follow the OS */ }
  PS.initTheme = function () {
    var b = PS.$("theme");
    if (!b) return;
    function currentTheme() {
      return document.documentElement.getAttribute("data-theme") ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    }
    function describeTheme() {
      var cur = currentTheme();
      b.setAttribute("aria-label", PS.t("theme") + ": " + (cur === "dark" ? "light" : "dark"));
      b.setAttribute("aria-pressed", String(cur === "dark"));
      b.title = "Current theme: " + cur;
    }
    describeTheme();
    b.addEventListener("click", function () {
      var cur = currentTheme();
      var next = cur === "dark" ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem("ps-theme", next); } catch (e) { /* ignore */ }
      describeTheme();
      window.dispatchEvent(new Event("resize"));
    });
  };

  // ---------- menu and footer ----------
  PS.menu = function () {
    var nav = PS.$("nav");
    if (!nav) return;
    var here = location.pathname.replace(/\/+$/, "") || "/";
    PAGES.forEach(function (p) {
      var a = PS.el("a", null, PS.t(p[1]));
      a.href = p[0];
      if (p[0] === here) a.setAttribute("aria-current", "page");
      nav.appendChild(a);
    });
  };
  PS.footer = function (extra) {
    var f = PS.$("foot");
    if (!f) return;
    f.textContent = "";
    var links = PS.el("p", "foot-links");
    PAGES.forEach(function (p) { var a = PS.el("a", null, PS.t(p[1])); a.href = p[0]; links.appendChild(a); });
    var g = PS.el("a", null, PS.t("sourceCode")); g.href = "https://github.com/IT25101414/price-signal"; links.appendChild(g);
    f.appendChild(links);
    f.appendChild(PS.el("p", null, PS.t("sourceNote") + (extra ? " " + extra : "")));
  };
  // Every page says so when the price history is invented (demo builds), so made-up prices are never mistaken for real ones.
  PS.demoNotice = function () {
    if (PS.$("demo")) return;                       // the Today page has its own notice
    fetch("/api/status").then(function (r) { return r.json(); }).then(function (s) {
      if (s.history_source !== "synthetic") return;
      var main = document.querySelector("main");
      if (!main) return;
      var p = PS.el("p", "demo", "Demo data: the price history on this page is invented for testing the layout, not Central Bank prices.");
      p.setAttribute("role", "note");
      main.insertBefore(p, main.firstChild);
    }).catch(function () {});
  };
  PS.start = function (extra) { PS.initLanguage(); PS.initTheme(); PS.menu(); PS.footer(extra); PS.demoNotice(); };

  // ---------- tooltip ----------
  var tip;
  PS.tip = function (x, y, nodes) {
    tip = tip || PS.$("tip");
    if (!tip) { tip = PS.el("div", "tip"); tip.id = "tip"; tip.setAttribute("role", "status"); document.body.appendChild(tip); }
    tip.textContent = "";
    nodes.forEach(function (n) { tip.appendChild(typeof n === "string" ? PS.el("div", null, n) : n); });
    tip.hidden = false;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(window.innerWidth - w - 8, Math.max(8, x + 14)) + "px";
    tip.style.top = Math.max(8, Math.min(window.innerHeight - h - 8, y - h - 10)) + "px";
  };
  PS.hideTip = function () { tip = tip || PS.$("tip"); if (tip) tip.hidden = true; };
  PS.tipRow = function (color, value, label) {
    var row = PS.el("div", "t-row"), k = PS.el("i");
    k.style.borderTopColor = "var(" + color + ")";
    row.appendChild(k); row.appendChild(PS.el("b", null, value)); row.appendChild(PS.el("span", null, label));
    return row;
  };

  // ---------- chart helpers ----------
  function niceStep(raw) {
    var p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10)), f = raw / p;
    return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 6.5 ? 5 : 10) * p;
  }
  PS.ticks = function (lo, hi, n) {
    if (hi === lo) { hi = lo + 1; }
    var step = niceStep((hi - lo) / (n || 4)), a = Math.floor(lo / step) * step, out = [];
    for (var v = a; v <= hi + step * 0.001; v += step) out.push(+v.toFixed(6));
    return out;
  };
  /* Draw into box now and again whenever its width changes, so text stays readable on a phone. */
  PS.responsive = function (box, draw) {
    var last = -1;
    function go() {
      var w = Math.floor(box.clientWidth);
      if (w === last || w < 60) return;
      last = w; box.textContent = ""; draw(w);
    }
    go();
    if (window.ResizeObserver) new ResizeObserver(go).observe(box); else window.addEventListener("resize", go);
    window.addEventListener("resize", function () { last = -1; go(); });
  };
  PS.legend = function (items) {
    var l = PS.el("div", "legend");
    items.forEach(function (x) {
      var i = PS.el("span"), k = PS.el("i");
      k.style.borderTopColor = "var(" + x.color + ")";
      if (x.dash) k.style.borderTopStyle = "dashed";
      i.appendChild(k); i.appendChild(document.createTextNode(x.label)); l.appendChild(i);
    });
    return l;
  };
  PS.table = function (summary, headers, rows) {
    var det = PS.el("details", "table");
    det.appendChild(PS.el("summary", null, summary));
    var box = PS.el("div", "tbl"), tb = PS.el("table"), tr = PS.el("tr");
    headers.forEach(function (h) { tr.appendChild(PS.el("th", null, h)); });
    tb.appendChild(tr);
    rows.forEach(function (r) {
      var t = PS.el("tr");
      r.forEach(function (c) { t.appendChild(PS.el("td", null, c)); });
      tb.appendChild(t);
    });
    box.appendChild(tb); det.appendChild(box);
    return det;
  };

  /* Line chart. o: {dates, series:[{label,color,values,fmt,dash}], width, height, axisFmt, ref:{value,label}, aria} */
  PS.lineChart = function (o) {
    var W = o.width, H = o.height || 260, L = 52, R = W < 520 ? 12 : 118, T = 12, B = 28, dates = o.dates;
    var vals = [];
    o.series.forEach(function (s) { s.values.forEach(function (v) { if (v != null) vals.push(v); }); });
    if (o.ref) vals.push(o.ref.value);
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), pad = (hi - lo) * 0.08 || 1;
    lo -= pad; hi += pad;
    if (o.floorZero && lo < 0) lo = 0;
    var ticks = PS.ticks(lo, hi, 4); lo = Math.min(lo, ticks[0]); hi = Math.max(hi, ticks[ticks.length - 1]);
    var X = function (i) { return L + (i / Math.max(1, dates.length - 1)) * (W - L - R); };
    var Y = function (v) { return T + (1 - (v - lo) / (hi - lo)) * (H - T - B); };
    var afmt = o.axisFmt || function (v) { return String(Math.round(v)); };
    var svg = PS.s("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": o.aria || "Line chart" });
    ticks.forEach(function (v) {
      var y = Y(v);
      svg.appendChild(PS.s("line", { x1: L, x2: W - R, y1: y, y2: y, stroke: "var(--line)", "stroke-width": 1 }));
      svg.appendChild(PS.s("text", { x: L - 8, y: y + 4, "text-anchor": "end", "font-size": 11, fill: "var(--ink-3)" }, afmt(v)));
    });
    var yr = dates.length > 150;
    [0, Math.floor((dates.length - 1) / 2), dates.length - 1].forEach(function (i, k) {
      svg.appendChild(PS.s("text", { x: X(i), y: H - 8, "text-anchor": k === 0 ? "start" : k === 2 ? "end" : "middle", "font-size": 11, fill: "var(--ink-3)" }, PS.date(dates[i], yr)));
    });
    if (o.ref) {
      var ry = Y(o.ref.value);
      svg.appendChild(PS.s("line", { x1: L, x2: W - R, y1: ry, y2: ry, stroke: "var(--ink-3)", "stroke-width": 1.5, "stroke-dasharray": "5 4" }));
      if (o.ref.label) svg.appendChild(PS.s("text", { x: W - R + 8, y: ry + 4, "font-size": 12, fill: "var(--ink-2)" }, o.ref.label));
    }
    var ends = [];
    o.series.forEach(function (s) {
      var pts = [], run = [];
      s.values.forEach(function (v, i) {
        if (v == null) { if (run.length) pts.push(run); run = []; return; }
        run.push(X(i).toFixed(1) + "," + Y(v).toFixed(1));
      });
      if (run.length) pts.push(run);
      pts.forEach(function (seg) {
        svg.appendChild(PS.s("polyline", { points: seg.join(" "), fill: "none", stroke: "var(" + s.color + ")", "stroke-width": 2, "stroke-linejoin": "round", "stroke-dasharray": s.dash || "none" }));
      });
      var li = -1;
      s.values.forEach(function (v, i) { if (v != null) li = i; });
      if (li >= 0) ends.push({ s: s, i: li, y: Y(s.values[li]), v: s.values[li] });
    });
    if (R > 60) {
      ends.sort(function (a, b) { return a.y - b.y; });
      for (var k = 1; k < ends.length; k++) if (ends[k].y - (ends[k - 1].ty != null ? ends[k - 1].ty : ends[k - 1].y) < 15) ends[k].ty = (ends[k - 1].ty != null ? ends[k - 1].ty : ends[k - 1].y) + 15;
    }
    ends.forEach(function (e) {
      svg.appendChild(PS.s("circle", { cx: X(e.i), cy: e.y, r: 4, fill: "var(" + e.s.color + ")", stroke: "var(--surface)", "stroke-width": 2 }));
      if (R > 60) svg.appendChild(PS.s("text", { x: W - R + 10, y: (e.ty != null ? e.ty : e.y) + 4, "font-size": 12, fill: "var(--ink)" }, e.s.label + " " + (e.s.fmt || afmt)(e.v)));
    });
    var cross = PS.s("line", { y1: T, y2: H - B, stroke: "var(--ink-3)", "stroke-width": 1, visibility: "hidden" });
    svg.appendChild(cross);
    var dots = o.series.map(function (s) { var c = PS.s("circle", { r: 4.5, fill: "var(" + s.color + ")", stroke: "var(--surface)", "stroke-width": 2, visibility: "hidden" }); svg.appendChild(c); return c; });
    function at(cx, cy) {
      var r = svg.getBoundingClientRect(), px = ((cx - r.left) / r.width) * W;
      var i = Math.max(0, Math.min(dates.length - 1, Math.round(((px - L) / (W - L - R)) * (dates.length - 1))));
      cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i)); cross.setAttribute("visibility", "visible");
      var rows = [PS.el("div", "t-d", PS.date(dates[i], true))];
      o.series.forEach(function (s, j) {
        var v = s.values[i];
        if (v == null) { dots[j].setAttribute("visibility", "hidden"); return; }
        dots[j].setAttribute("cx", X(i)); dots[j].setAttribute("cy", Y(v)); dots[j].setAttribute("visibility", "visible");
        rows.push(PS.tipRow(s.color, (s.fmt || afmt)(v), s.label));
      });
      PS.tip(cx, cy, rows);
    }
    svg.addEventListener("pointermove", function (e) { at(e.clientX, e.clientY); });
    svg.addEventListener("pointerleave", function () { PS.hideTip(); cross.setAttribute("visibility", "hidden"); dots.forEach(function (d) { d.setAttribute("visibility", "hidden"); }); });
    return svg;
  };

  /* Tiny two-line chart for small multiples. values arrays share one x axis; band marks the last n points. */
  PS.spark = function (w, h, series, band) {
    var all = [];
    series.forEach(function (s) { s.values.forEach(function (v) { if (v != null) all.push(v); }); });
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all), pad = (hi - lo) * 0.12 || 1; lo -= pad; hi += pad;
    var n = series[0].values.length, X = function (i) { return 4 + (i / (n - 1)) * (w - 8); }, Y = function (v) { return 4 + (1 - (v - lo) / (hi - lo)) * (h - 8); };
    var svg = PS.s("svg", { width: w, height: h, viewBox: "0 0 " + w + " " + h, "aria-hidden": "true" });
    if (band) svg.appendChild(PS.s("rect", { x: X(n - band), y: 0, width: w - X(n - band), height: h, fill: "var(--accent-soft)", opacity: 0.55 }));
    series.forEach(function (s) {
      var pts = [];
      function flush() {
        if (pts.length > 1) svg.appendChild(PS.s("polyline", { points: pts.join(" "), fill: "none", stroke: "var(" + s.color + ")", "stroke-width": 2, "stroke-linejoin": "round" }));
        else if (pts.length === 1) {
          var xy = pts[0].split(",");
          svg.appendChild(PS.s("circle", { cx: xy[0], cy: xy[1], r: 2, fill: "var(" + s.color + ")" }));
        }
        pts = [];
      }
      s.values.forEach(function (v, i) {
        if (v == null) flush();
        else pts.push(X(i).toFixed(1) + "," + Y(v).toFixed(1));
      });
      flush();
    });
    return svg;
  };
})();
