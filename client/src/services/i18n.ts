export type Language = 'en' | 'te' | 'hi';

export interface UIStrings {
  appTitle: string;
  tagline: string;
  allLocalities: string;
  overallHyderabad: string;
  overallHyderabadDesc: string;
  resetToCitywide: string;
  feedTab: string;
  mapTab: string;
  adminTab: string;
  modelsTab: string;
  searchPlaceholder: string;
  alertsFound: string;
  allCategories: string;
  catRoadClosure: string;
  catWaterSupply: string;
  catPowerCut: string;
  catSevereWeather: string;
  catPublicService: string;
  catOther: string;
  allSeverities: string;
  sevCritical: string;
  sevWarning: string;
  sevAdvisory: string;
  sevInfo: string;
  statusAll: string;
  statusActive: string;
  statusUpcoming: string;
  statusPast: string;
  expectedImpact: string;
  recommendedActions: string;
  officialBadge: string;
  newsBadge: string;
  unverifiedBadge: string;
  unverifiedWarningTitle: string;
  unverifiedWarningBody: string;
  voiceReadout: string;
  stopAudio: string;
  feedbackButton: string;
  communityResolved: string;
  communityActive: string;
  disclaimer: string;
  loadingAlerts: string;
  noAlertsFound: string;
  resetAllFilters: string;
  published: string;
  immediate: string;
}

export const I18N: Record<Language, UIStrings> = {
  en: {
    appTitle: 'CivicPulse',
    tagline: 'Hyperlocal Actionable Civic Alerts',
    allLocalities: 'All Hyderabad Localities',
    overallHyderabad: 'Overall Hyderabad (All Zones)',
    overallHyderabadDesc: 'Show all municipal alerts across Greater Hyderabad',
    resetToCitywide: 'Reset to Overall Hyderabad',
    feedTab: 'Feed View',
    mapTab: 'Live Map',
    adminTab: 'Admin & Ingest',
    modelsTab: 'Model Hub',
    searchPlaceholder: 'Search alerts by title or keywords...',
    alertsFound: 'alerts found',
    allCategories: 'All Categories',
    catRoadClosure: 'Road Closures',
    catWaterSupply: 'Water Supply',
    catPowerCut: 'Power Cuts',
    catSevereWeather: 'Severe Weather',
    catPublicService: 'Public Services',
    catOther: 'Other',
    allSeverities: 'All Severities',
    sevCritical: 'Critical',
    sevWarning: 'Warning',
    sevAdvisory: 'Advisory',
    sevInfo: 'Info',
    statusAll: 'All Time',
    statusActive: 'Active',
    statusUpcoming: 'Upcoming',
    statusPast: 'Past',
    expectedImpact: 'Expected Impact',
    recommendedActions: 'Recommended Actions Checklist',
    officialBadge: 'Official',
    newsBadge: 'Verified News',
    unverifiedBadge: 'Unverified',
    unverifiedWarningTitle: 'Unverified Public Report:',
    unverifiedWarningBody: 'This announcement originated from an informal source and has not yet received official municipal corroboration.',
    voiceReadout: 'Voice Readout',
    stopAudio: 'Stop Audio',
    feedbackButton: 'Wrong category or severity?',
    communityResolved: 'Resolved',
    communityActive: 'Still Active',
    disclaimer: '⚠️ Disclaimer: Summaries are AI-generated and automatically extracted from official announcements and local feeds. Always verify with municipal authorities for life-safety emergencies.',
    loadingAlerts: 'Loading hyperlocal verified alerts from pipeline...',
    noAlertsFound: 'No matching alerts found',
    resetAllFilters: 'Reset All Filters',
    published: 'Published',
    immediate: 'Immediate',
  },
  te: {
    appTitle: 'సివిక్ పల్స్',
    tagline: 'హైదరాబాద్ స్థానిక పౌర హెచ్చరికలు',
    allLocalities: 'హైదరాబాద్ సమగ్ర ప్రాంతాలు',
    overallHyderabad: 'మొత్తం హైదరాబాద్ (అన్ని ప్రాంతాలు)',
    overallHyderabadDesc: 'గ్రేటర్ హైదరాబాద్ పరిధిలోని అన్ని మున్సిపల్ హెచ్చరికలు',
    resetToCitywide: 'మొత్తం హైదరాబాద్‌కు రీసెట్ చేయండి',
    feedTab: 'హెచ్చరికలు (ఫీడ్)',
    mapTab: 'లైవ్ మ్యాప్',
    adminTab: 'అడ్మిన్ & ఇన్‌జెస్ట్',
    modelsTab: 'మోడల్ హబ్',
    searchPlaceholder: 'హెచ్చరికలు లేదా ప్రాంతాన్ని శోధించండి...',
    alertsFound: 'హెచ్చరికలు కనుగొనబడ్డాయి',
    allCategories: 'అన్ని విభాగాలు',
    catRoadClosure: 'రోడ్డు మూసివేత',
    catWaterSupply: 'మంచినీటి సరఫరా',
    catPowerCut: 'విద్యుత్ కోత',
    catSevereWeather: 'భారీ వర్షాలు',
    catPublicService: 'పౌర సేవలు',
    catOther: 'ఇతర నోటీసులు',
    allSeverities: 'అన్ని తీవ్రతలు',
    sevCritical: 'అత్యవసరం',
    sevWarning: 'హెచ్చరిక',
    sevAdvisory: 'సలహా',
    sevInfo: 'సమాచారం',
    statusAll: 'అన్ని వేళలా',
    statusActive: 'ప్రస్తుతం యాక్టివ్',
    statusUpcoming: 'రాబోయేవి',
    statusPast: 'ముగిసినవి',
    expectedImpact: 'ఆశించిన ప్రభావం',
    recommendedActions: 'పౌరులు చేయవలసిన పనుల జాబితా',
    officialBadge: 'అధికారికం',
    newsBadge: 'ధృవీకరించిన వార్త',
    unverifiedBadge: 'ధృవీకరించబడనిది',
    unverifiedWarningTitle: 'ధృవీకరించబడని పౌర సమాచారం:',
    unverifiedWarningBody: 'ఈ సమాచారం అధికారిక మున్సిపల్ సంస్థల ద్వారా ఇంకా పూర్తిగా నిర్ధారించబడలేదు. విచక్షణతో వ్యవహరించగలరు.',
    voiceReadout: 'వాయిస్ వినండి',
    stopAudio: 'ఆడియో ఆపండి',
    feedbackButton: 'సరియైన విభాగం లేదా తీవ్రత కాదా?',
    communityResolved: 'పునరుద్ధరించబడింది',
    communityActive: 'ఇంకా రాలేదు',
    disclaimer: '⚠️ గమనిక: ఈ హెచ్చరికలు మున్సిపల్ బులెటిన్ల నుండి ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ ద్వారా సంగ్రహించబడ్డాయి. అత్యవసర సమయాల్లో అధికారిక విభాగాన్ని సంప్రదించండి.',
    loadingAlerts: 'స్థానిక హెచ్చరికలను లోడ్ చేస్తున్నాము...',
    noAlertsFound: 'హెచ్చరికలు ఏవీ కనుగొనబడలేదు',
    resetAllFilters: 'అన్ని ఫిల్టర్లను రీసెట్ చేయండి',
    published: 'ప్రచురించబడింది',
    immediate: 'వెంటనే అమలు',
  },
  hi: {
    appTitle: 'सिविक पल्स',
    tagline: 'हैदराबाद स्थानीय नागरिक अलर्ट',
    allLocalities: 'समग्र हैदराबाद (सभी क्षेत्र)',
    overallHyderabad: 'समग्र हैदराबाद (सभी ज़ोन)',
    overallHyderabadDesc: 'ग्रेटर हैदराबाद के सभी नागरिक अलर्ट देखें',
    resetToCitywide: 'समग्र हैदराबाद पर रीसेट करें',
    feedTab: 'अलर्ट फ़ीड',
    mapTab: 'लाइव मैप',
    adminTab: 'एडमिन एवं इनजेस्ट',
    modelsTab: 'मॉडल हब',
    searchPlaceholder: 'अलर्ट या क्षेत्र खोजें...',
    alertsFound: 'अलर्ट उपलब्ध',
    allCategories: 'सभी श्रेणियां',
    catRoadClosure: 'सड़क बंदी',
    catWaterSupply: 'जलापूर्ति',
    catPowerCut: 'बिजली कटौती',
    catSevereWeather: 'खराब मौसम',
    catPublicService: 'नागरिक सेवाएं',
    catOther: 'अन्य सूचनाएं',
    allSeverities: 'सभी तीव्रता',
    sevCritical: 'अति गंभीर',
    sevWarning: 'चेतावनी',
    sevAdvisory: 'परामर्श',
    sevInfo: 'सूचना',
    statusAll: 'सभी समय',
    statusActive: 'सक्रिय अलर्ट',
    statusUpcoming: 'आगामी',
    statusPast: 'समाप्त',
    expectedImpact: 'अपेक्षित प्रभाव',
    recommendedActions: 'अनुशंसित नागरिक कार्रवाई चेकलिस्ट',
    officialBadge: 'आधिकारिक',
    newsBadge: 'सत्यापित समाचार',
    unverifiedBadge: 'असत्यापित',
    unverifiedWarningTitle: 'असत्यापित सार्वजनिक सूचना:',
    unverifiedWarningBody: 'यह घोषणा अनौपचारिक स्रोत से आई है और अभी तक नगर निगम द्वारा इसकी आधिकारिक पुष्टि नहीं हुई है।',
    voiceReadout: 'आवाज़ सुनें',
    stopAudio: 'ऑडियो बंद करें',
    feedbackButton: 'गलत श्रेणी या गंभीरता?',
    communityResolved: 'बहाल हुआ',
    communityActive: 'अभी भी बंद',
    disclaimer: '⚠️ अस्वीकरण: यह सारांश नगर निगम घोषणाओं से AI द्वारा तैयार किया गया है। आपातकालीन स्थिति में आधिकारिक विभाग से पुष्टि करें।',
    loadingAlerts: 'हैदराबाद के स्थानीय अलर्ट लोड हो रहे हैं...',
    noAlertsFound: 'कोई अलर्ट नहीं मिला',
    resetAllFilters: 'फ़िल्टर रीसेट करें',
    published: 'प्रकाशित',
    immediate: 'तत्काल',
  },
};
