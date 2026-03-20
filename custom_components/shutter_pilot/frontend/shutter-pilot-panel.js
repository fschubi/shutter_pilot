/**
 * Shutter Pilot – Home Assistant Sidebar Panel v4
 * Multi-language (DE/EN/FR/ES/IT) · Tabs: Dashboard | Areas | Shutters
 */
const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace") ?? customElements.get("hui-view")
);
const html = LitElement?.prototype?.html ?? ((s,...v)=>s.reduce((a,b,i)=>a+v[i-1]+b));
const css  = LitElement?.prototype?.css  ?? ((s)=>s);

const MODE_ICONS = {time:"mdi:clock-outline",brightness:"mdi:white-balance-sunny",sun:"mdi:weather-sunset"};
const WIN_OPEN_OPTS = ["on","open","true","offen"];
const WIN_TILT_OPTS = ["none","tilted","gekippt","kipp","2"];

/* ─── i18n ─── */
const I18N = {
de:{
  tab_dashboard:"Dashboard",tab_areas:"Bereiche",tab_shutters:"Rollläden",
  subtitle:"{a} Bereiche, {s} Rollläden",
  loading:"Laden…",
  mode_time:"Zeit",mode_brightness:"Helligkeit",mode_sun:"Sonnenstand",
  shutter_s:"Rollladen",no_shutters:"Keine Rollläden",
  auto:"Automatik",
  btn_up:"Hoch",btn_stop:"Stop",btn_down:"Runter",btn_sun:"Sonnenschutz",
  btn_add:"hinzufügen",btn_save:"Speichern",btn_cancel:"Abbrechen",
  empty_areas:"Keine Bereiche konfiguriert. Wechsle zum Tab \"Bereiche\".",
  empty_areas_list:"Noch keine Bereiche angelegt.",
  empty_shutters_list:"Noch keine Rollläden angelegt.",
  add_area:"Bereich hinzufügen",edit_area:"Bereich bearbeiten",
  add_shutter:"Rollladen hinzufügen",edit_shutter:"Rollladen bearbeiten",
  col_name:"Name",col_id:"ID",col_mode:"Modus",col_shutters:"Rollläden",
  col_cover:"Cover-Entity",col_area_up:"Bereich Hoch",col_area_down:"Bereich Runter",col_window:"Fenster",
  f_name:"Name",f_mode:"Steuerungsmodus",
  f_drive_delay:"Verzögerung zwischen Rollläden (Sek.)",
  f_sun_protect:"Sonnenschutz aktivieren",f_elev_thresh:"Elevation-Schwellwert (°)",
  f_light_entity:"Lampe/Schalter bei Runter (optional)",f_light_brightness:"Lampe Helligkeit (%)",
  f_time_up:"Woche Hoch",f_time_down:"Woche Runter",
  f_time_we_up:"Wochenende Hoch",f_time_we_down:"Wochenende Runter",
  f_sunrise_off:"Offset Sonnenaufgang (Min.)",f_sunset_off:"Offset Sonnenuntergang (Min.)",
  sun_next_rise:"Nächster Sonnenaufgang",sun_next_set:"Nächster Sonnenuntergang",
  sun_trigger_up:"Hoch-Fahrt um",sun_trigger_down:"Runter-Fahrt um",
  sun_elevation:"Aktuelle Elevation",sun_offset:"Offset",
  f_brightness_sensor:"Helligkeitssensor",f_lux_up:"Lux Hoch-Schwelle",f_lux_down:"Lux Runter-Schwelle",
  f_w_up_from:"Woche Hoch ab",f_w_up_to:"Woche Hoch bis",f_w_down_from:"Woche Runter ab",f_w_down_to:"Woche Runter bis",
  f_we_up_from:"WE Hoch ab",f_we_up_to:"WE Hoch bis",f_we_down_from:"WE Runter ab",f_we_down_to:"WE Runter bis",
  f_cover:"Rollladen / Cover",f_window_sensor:"Fenster-/Türsensor (optional)",
  f_win_open:"Fenster-Status 'offen'",f_win_tilt:"Fenster-Status 'gekippt'",
  f_win_tilt_none:"Deaktiviert (kein Kipp-Status)",
  f_pos_win_open:"Position bei Fenster offen",f_pos_win_tilt:"Position bei Fenster gekippt",
  f_lock:"Aussperrschutz (verhindert vollständiges Schließen bei offener Tür)",
  f_min_pos:"Mindest-Position wenn Tür offen",
  f_area_up:"Bereich (Hoch)",f_area_down:"Bereich (Runter)",
  f_pos_open:"Position Offen",f_pos_closed:"Position Geschlossen",f_pos_sun:"Sonnenschutz-Position",
  f_drive_after:"Nachholen wenn Fenster offen",
  f_drive_after_hint:"Wenn die Schließzeit erreicht wird aber das Fenster noch offen ist, wird die Fahrt nachgeholt sobald das Fenster geschlossen wird.",
  pick_entity:"Entität auswählen…",
  confirm_del_area:"Bereich \"{id}\" wirklich löschen?",confirm_del_shutter:"Rollladen wirklich löschen?",
},
en:{
  tab_dashboard:"Dashboard",tab_areas:"Areas",tab_shutters:"Shutters",
  subtitle:"{a} areas, {s} shutters",
  loading:"Loading…",
  mode_time:"Time",mode_brightness:"Brightness",mode_sun:"Sun position",
  shutter_s:"shutter",no_shutters:"No shutters",
  auto:"Automation",
  btn_up:"Up",btn_stop:"Stop",btn_down:"Down",btn_sun:"Sun protect",
  btn_add:"Add",btn_save:"Save",btn_cancel:"Cancel",
  empty_areas:"No areas configured. Switch to the \"Areas\" tab.",
  empty_areas_list:"No areas created yet.",
  empty_shutters_list:"No shutters created yet.",
  add_area:"Add area",edit_area:"Edit area",
  add_shutter:"Add shutter",edit_shutter:"Edit shutter",
  col_name:"Name",col_id:"ID",col_mode:"Mode",col_shutters:"Shutters",
  col_cover:"Cover entity",col_area_up:"Area Up",col_area_down:"Area Down",col_window:"Window",
  f_name:"Name",f_mode:"Control mode",
  f_drive_delay:"Delay between shutters (sec.)",
  f_sun_protect:"Enable sun protection",f_elev_thresh:"Elevation threshold (°)",
  f_light_entity:"Light/switch on close (optional)",f_light_brightness:"Light brightness (%)",
  f_time_up:"Weekday Up",f_time_down:"Weekday Down",
  f_time_we_up:"Weekend Up",f_time_we_down:"Weekend Down",
  f_sunrise_off:"Sunrise offset (min.)",f_sunset_off:"Sunset offset (min.)",
  sun_next_rise:"Next sunrise",sun_next_set:"Next sunset",
  sun_trigger_up:"Up trigger at",sun_trigger_down:"Down trigger at",
  sun_elevation:"Current elevation",sun_offset:"Offset",
  f_brightness_sensor:"Brightness sensor",f_lux_up:"Lux up threshold",f_lux_down:"Lux down threshold",
  f_w_up_from:"Weekday up from",f_w_up_to:"Weekday up to",f_w_down_from:"Weekday down from",f_w_down_to:"Weekday down to",
  f_we_up_from:"Weekend up from",f_we_up_to:"Weekend up to",f_we_down_from:"Weekend down from",f_we_down_to:"Weekend down to",
  f_cover:"Shutter / Cover",f_window_sensor:"Window/door sensor (optional)",
  f_win_open:"Window state 'open'",f_win_tilt:"Window state 'tilted'",
  f_win_tilt_none:"Disabled (no tilt state)",
  f_pos_win_open:"Position when window open",f_pos_win_tilt:"Position when window tilted",
  f_lock:"Lock protection (prevents full close when door is open)",
  f_min_pos:"Minimum position when door open",
  f_area_up:"Area (Up)",f_area_down:"Area (Down)",
  f_pos_open:"Position Open",f_pos_closed:"Position Closed",f_pos_sun:"Sun protection position",
  f_drive_after:"Catch up when window open",
  f_drive_after_hint:"When close time is reached but the window is still open, the drive will be executed as soon as the window is closed.",
  pick_entity:"Select entity…",
  confirm_del_area:"Really delete area \"{id}\"?",confirm_del_shutter:"Really delete shutter?",
},
fr:{
  tab_dashboard:"Tableau de bord",tab_areas:"Zones",tab_shutters:"Volets",
  subtitle:"{a} zones, {s} volets",loading:"Chargement…",
  mode_time:"Horaire",mode_brightness:"Luminosité",mode_sun:"Position solaire",
  shutter_s:"volet",no_shutters:"Aucun volet",auto:"Automatique",
  btn_up:"Monter",btn_stop:"Stop",btn_down:"Descendre",btn_sun:"Protection solaire",
  btn_add:"Ajouter",btn_save:"Enregistrer",btn_cancel:"Annuler",
  empty_areas:"Aucune zone configurée.",empty_areas_list:"Aucune zone créée.",empty_shutters_list:"Aucun volet créé.",
  add_area:"Ajouter zone",edit_area:"Modifier zone",add_shutter:"Ajouter volet",edit_shutter:"Modifier volet",
  col_name:"Nom",col_id:"ID",col_mode:"Mode",col_shutters:"Volets",
  col_cover:"Entité cover",col_area_up:"Zone Montée",col_area_down:"Zone Descente",col_window:"Fenêtre",
  f_name:"Nom",f_mode:"Mode de contrôle",f_drive_delay:"Délai entre volets (sec.)",
  f_sun_protect:"Protection solaire",f_elev_thresh:"Seuil élévation (°)",
  f_light_entity:"Lampe/interrupteur descente",f_light_brightness:"Luminosité lampe (%)",
  f_time_up:"Semaine montée",f_time_down:"Semaine descente",
  f_time_we_up:"Week-end montée",f_time_we_down:"Week-end descente",
  f_sunrise_off:"Décalage lever (min.)",f_sunset_off:"Décalage coucher (min.)",
  sun_next_rise:"Prochain lever",sun_next_set:"Prochain coucher",
  sun_trigger_up:"Montée à",sun_trigger_down:"Descente à",
  sun_elevation:"Élévation actuelle",sun_offset:"Décalage",
  f_brightness_sensor:"Capteur luminosité",f_lux_up:"Seuil lux montée",f_lux_down:"Seuil lux descente",
  f_w_up_from:"Sem. montée de",f_w_up_to:"Sem. montée à",f_w_down_from:"Sem. descente de",f_w_down_to:"Sem. descente à",
  f_we_up_from:"WE montée de",f_we_up_to:"WE montée à",f_we_down_from:"WE descente de",f_we_down_to:"WE descente à",
  f_cover:"Volet / Cover",f_window_sensor:"Capteur fenêtre (optionnel)",
  f_win_open:"État fenêtre 'ouverte'",f_win_tilt:"État fenêtre 'basculée'",f_win_tilt_none:"Désactivé",
  f_pos_win_open:"Position fenêtre ouverte",f_pos_win_tilt:"Position fenêtre basculée",
  f_lock:"Protection anti-enfermement",f_min_pos:"Position min. porte ouverte",
  f_area_up:"Zone (Montée)",f_area_down:"Zone (Descente)",
  f_pos_open:"Position Ouvert",f_pos_closed:"Position Fermé",f_pos_sun:"Position protection solaire",
  f_drive_after:"Rattraper si fenêtre ouverte",f_drive_after_hint:"La commande sera exécutée dès que la fenêtre sera fermée.",
  pick_entity:"Sélectionner…",confirm_del_area:"Supprimer la zone \"{id}\" ?",confirm_del_shutter:"Supprimer le volet ?",
},
es:{
  tab_dashboard:"Panel",tab_areas:"Zonas",tab_shutters:"Persianas",
  subtitle:"{a} zonas, {s} persianas",loading:"Cargando…",
  mode_time:"Horario",mode_brightness:"Brillo",mode_sun:"Posición solar",
  shutter_s:"persiana",no_shutters:"Sin persianas",auto:"Automático",
  btn_up:"Subir",btn_stop:"Parar",btn_down:"Bajar",btn_sun:"Protección solar",
  btn_add:"Añadir",btn_save:"Guardar",btn_cancel:"Cancelar",
  empty_areas:"No hay zonas configuradas.",empty_areas_list:"No hay zonas.",empty_shutters_list:"No hay persianas.",
  add_area:"Añadir zona",edit_area:"Editar zona",add_shutter:"Añadir persiana",edit_shutter:"Editar persiana",
  col_name:"Nombre",col_id:"ID",col_mode:"Modo",col_shutters:"Persianas",
  col_cover:"Entidad cover",col_area_up:"Zona Subida",col_area_down:"Zona Bajada",col_window:"Ventana",
  f_name:"Nombre",f_mode:"Modo de control",f_drive_delay:"Retraso entre persianas (seg.)",
  f_sun_protect:"Protección solar",f_elev_thresh:"Umbral elevación (°)",
  f_light_entity:"Luz/interruptor al bajar",f_light_brightness:"Brillo luz (%)",
  f_time_up:"L-V subida",f_time_down:"L-V bajada",
  f_time_we_up:"Fin de semana subida",f_time_we_down:"Fin de semana bajada",
  f_sunrise_off:"Desfase amanecer (min.)",f_sunset_off:"Desfase atardecer (min.)",
  sun_next_rise:"Próximo amanecer",sun_next_set:"Próximo atardecer",
  sun_trigger_up:"Subida a las",sun_trigger_down:"Bajada a las",
  sun_elevation:"Elevación actual",sun_offset:"Desfase",
  f_brightness_sensor:"Sensor brillo",f_lux_up:"Umbral lux subida",f_lux_down:"Umbral lux bajada",
  f_w_up_from:"L-V subida desde",f_w_up_to:"L-V subida hasta",f_w_down_from:"L-V bajada desde",f_w_down_to:"L-V bajada hasta",
  f_we_up_from:"Fin sem. subida desde",f_we_up_to:"Fin sem. subida hasta",f_we_down_from:"Fin sem. bajada desde",f_we_down_to:"Fin sem. bajada hasta",
  f_cover:"Persiana / Cover",f_window_sensor:"Sensor ventana (opcional)",
  f_win_open:"Estado ventana 'abierta'",f_win_tilt:"Estado ventana 'inclinada'",f_win_tilt_none:"Desactivado",
  f_pos_win_open:"Posición ventana abierta",f_pos_win_tilt:"Posición ventana inclinada",
  f_lock:"Protección anti-bloqueo",f_min_pos:"Posición mín. puerta abierta",
  f_area_up:"Zona (Subida)",f_area_down:"Zona (Bajada)",
  f_pos_open:"Posición Abierta",f_pos_closed:"Posición Cerrada",f_pos_sun:"Posición protección solar",
  f_drive_after:"Recuperar si ventana abierta",f_drive_after_hint:"Se ejecutará cuando la ventana se cierre.",
  pick_entity:"Seleccionar…",confirm_del_area:"¿Eliminar zona \"{id}\"?",confirm_del_shutter:"¿Eliminar persiana?",
},
it:{
  tab_dashboard:"Pannello",tab_areas:"Zone",tab_shutters:"Tapparelle",
  subtitle:"{a} zone, {s} tapparelle",loading:"Caricamento…",
  mode_time:"Orario",mode_brightness:"Luminosità",mode_sun:"Posizione solare",
  shutter_s:"tapparella",no_shutters:"Nessuna tapparella",auto:"Automatico",
  btn_up:"Su",btn_stop:"Stop",btn_down:"Giù",btn_sun:"Protezione solare",
  btn_add:"Aggiungi",btn_save:"Salva",btn_cancel:"Annulla",
  empty_areas:"Nessuna zona configurata.",empty_areas_list:"Nessuna zona creata.",empty_shutters_list:"Nessuna tapparella.",
  add_area:"Aggiungi zona",edit_area:"Modifica zona",add_shutter:"Aggiungi tapparella",edit_shutter:"Modifica tapparella",
  col_name:"Nome",col_id:"ID",col_mode:"Modalità",col_shutters:"Tapparelle",
  col_cover:"Entità cover",col_area_up:"Zona Su",col_area_down:"Zona Giù",col_window:"Finestra",
  f_name:"Nome",f_mode:"Modalità",f_drive_delay:"Ritardo tra tapparelle (sec.)",
  f_sun_protect:"Protezione solare",f_elev_thresh:"Soglia elevazione (°)",
  f_light_entity:"Luce/interruttore alla chiusura",f_light_brightness:"Luminosità luce (%)",
  f_time_up:"Feriale apertura",f_time_down:"Feriale chiusura",
  f_time_we_up:"Weekend apertura",f_time_we_down:"Weekend chiusura",
  f_sunrise_off:"Offset alba (min.)",f_sunset_off:"Offset tramonto (min.)",
  sun_next_rise:"Prossima alba",sun_next_set:"Prossimo tramonto",
  sun_trigger_up:"Apertura alle",sun_trigger_down:"Chiusura alle",
  sun_elevation:"Elevazione attuale",sun_offset:"Offset",
  f_brightness_sensor:"Sensore luminosità",f_lux_up:"Soglia lux apertura",f_lux_down:"Soglia lux chiusura",
  f_w_up_from:"Feriale su da",f_w_up_to:"Feriale su a",f_w_down_from:"Feriale giù da",f_w_down_to:"Feriale giù a",
  f_we_up_from:"Weekend su da",f_we_up_to:"Weekend su a",f_we_down_from:"Weekend giù da",f_we_down_to:"Weekend giù a",
  f_cover:"Tapparella / Cover",f_window_sensor:"Sensore finestra (opzionale)",
  f_win_open:"Stato finestra 'aperta'",f_win_tilt:"Stato finestra 'ribaltata'",f_win_tilt_none:"Disattivato",
  f_pos_win_open:"Posizione finestra aperta",f_pos_win_tilt:"Posizione finestra ribaltata",
  f_lock:"Protezione anti-blocco",f_min_pos:"Posizione min. porta aperta",
  f_area_up:"Zona (Su)",f_area_down:"Zona (Giù)",
  f_pos_open:"Posizione Aperta",f_pos_closed:"Posizione Chiusa",f_pos_sun:"Posizione protezione solare",
  f_drive_after:"Recupera se finestra aperta",f_drive_after_hint:"Verrà eseguito alla chiusura della finestra.",
  pick_entity:"Seleziona…",confirm_del_area:"Eliminare zona \"{id}\"?",confirm_del_shutter:"Eliminare tapparella?",
},
nl:{
  tab_dashboard:"Dashboard",tab_areas:"Zones",tab_shutters:"Rolluiken",
  subtitle:"{a} zones, {s} rolluiken",loading:"Laden…",
  mode_time:"Tijd",mode_brightness:"Helderheid",mode_sun:"Zonnestand",
  shutter_s:"rolluik",no_shutters:"Geen rolluiken",auto:"Automatisch",
  btn_up:"Omhoog",btn_stop:"Stop",btn_down:"Omlaag",btn_sun:"Zonwering",
  btn_add:"Toevoegen",btn_save:"Opslaan",btn_cancel:"Annuleren",
  empty_areas:"Geen zones geconfigureerd. Ga naar het tabblad \"Zones\".",
  empty_areas_list:"Nog geen zones aangemaakt.",empty_shutters_list:"Nog geen rolluiken aangemaakt.",
  add_area:"Zone toevoegen",edit_area:"Zone bewerken",add_shutter:"Rolluik toevoegen",edit_shutter:"Rolluik bewerken",
  col_name:"Naam",col_id:"ID",col_mode:"Modus",col_shutters:"Rolluiken",
  col_cover:"Cover-entiteit",col_area_up:"Zone Omhoog",col_area_down:"Zone Omlaag",col_window:"Raam",
  f_name:"Naam",f_mode:"Besturingsmodus",f_drive_delay:"Vertraging tussen rolluiken (sec.)",
  f_sun_protect:"Zonwering inschakelen",f_elev_thresh:"Elevatiedrempel (°)",
  f_light_entity:"Lamp/schakelaar bij sluiten (optioneel)",f_light_brightness:"Lamp helderheid (%)",
  f_time_up:"Doordeweeks omhoog",f_time_down:"Doordeweeks omlaag",
  f_time_we_up:"Weekend omhoog",f_time_we_down:"Weekend omlaag",
  f_sunrise_off:"Offset zonsopgang (min.)",f_sunset_off:"Offset zonsondergang (min.)",
  sun_next_rise:"Volgende zonsopgang",sun_next_set:"Volgende zonsondergang",
  sun_trigger_up:"Omhoog om",sun_trigger_down:"Omlaag om",
  sun_elevation:"Huidige elevatie",sun_offset:"Offset",
  f_brightness_sensor:"Helderheidssensor",f_lux_up:"Lux omhoog drempel",f_lux_down:"Lux omlaag drempel",
  f_w_up_from:"Doordeweeks omhoog van",f_w_up_to:"Doordeweeks omhoog tot",f_w_down_from:"Doordeweeks omlaag van",f_w_down_to:"Doordeweeks omlaag tot",
  f_we_up_from:"Weekend omhoog van",f_we_up_to:"Weekend omhoog tot",f_we_down_from:"Weekend omlaag van",f_we_down_to:"Weekend omlaag tot",
  f_cover:"Rolluik / Cover",f_window_sensor:"Raam-/deursensor (optioneel)",
  f_win_open:"Raamstatus 'open'",f_win_tilt:"Raamstatus 'gekanteld'",f_win_tilt_none:"Uitgeschakeld (geen kantelstatus)",
  f_pos_win_open:"Positie bij raam open",f_pos_win_tilt:"Positie bij raam gekanteld",
  f_lock:"Buitensluitbeveiliging (voorkomt volledig sluiten bij open deur)",f_min_pos:"Minimumpositie bij open deur",
  f_area_up:"Zone (Omhoog)",f_area_down:"Zone (Omlaag)",
  f_pos_open:"Positie Open",f_pos_closed:"Positie Gesloten",f_pos_sun:"Zonweringpositie",
  f_drive_after:"Inhalen als raam open",f_drive_after_hint:"Als de sluitingstijd bereikt wordt maar het raam nog open is, wordt de actie uitgevoerd zodra het raam gesloten wordt.",
  pick_entity:"Entiteit selecteren…",confirm_del_area:"Zone \"{id}\" echt verwijderen?",confirm_del_shutter:"Rolluik echt verwijderen?",
},
da:{
  tab_dashboard:"Dashboard",tab_areas:"Områder",tab_shutters:"Persienner",
  subtitle:"{a} områder, {s} persienner",loading:"Indlæser…",
  mode_time:"Tid",mode_brightness:"Lysstyrke",mode_sun:"Solposition",
  shutter_s:"persienne",no_shutters:"Ingen persienner",auto:"Automatik",
  btn_up:"Op",btn_stop:"Stop",btn_down:"Ned",btn_sun:"Solbeskyttelse",
  btn_add:"Tilføj",btn_save:"Gem",btn_cancel:"Annuller",
  empty_areas:"Ingen områder konfigureret. Skift til fanen \"Områder\".",
  empty_areas_list:"Ingen områder oprettet endnu.",empty_shutters_list:"Ingen persienner oprettet endnu.",
  add_area:"Tilføj område",edit_area:"Rediger område",add_shutter:"Tilføj persienne",edit_shutter:"Rediger persienne",
  col_name:"Navn",col_id:"ID",col_mode:"Tilstand",col_shutters:"Persienner",
  col_cover:"Cover-entitet",col_area_up:"Område Op",col_area_down:"Område Ned",col_window:"Vindue",
  f_name:"Navn",f_mode:"Styringstilstand",f_drive_delay:"Forsinkelse mellem persienner (sek.)",
  f_sun_protect:"Aktivér solbeskyttelse",f_elev_thresh:"Elevationstærskel (°)",
  f_light_entity:"Lampe/kontakt ved lukning (valgfrit)",f_light_brightness:"Lampe lysstyrke (%)",
  f_time_up:"Hverdag op",f_time_down:"Hverdag ned",
  f_time_we_up:"Weekend op",f_time_we_down:"Weekend ned",
  f_sunrise_off:"Solopgang offset (min.)",f_sunset_off:"Solnedgang offset (min.)",
  sun_next_rise:"Næste solopgang",sun_next_set:"Næste solnedgang",
  sun_trigger_up:"Op kl.",sun_trigger_down:"Ned kl.",
  sun_elevation:"Aktuel elevation",sun_offset:"Offset",
  f_brightness_sensor:"Lyssensor",f_lux_up:"Lux op-tærskel",f_lux_down:"Lux ned-tærskel",
  f_w_up_from:"Hverdag op fra",f_w_up_to:"Hverdag op til",f_w_down_from:"Hverdag ned fra",f_w_down_to:"Hverdag ned til",
  f_we_up_from:"Weekend op fra",f_we_up_to:"Weekend op til",f_we_down_from:"Weekend ned fra",f_we_down_to:"Weekend ned til",
  f_cover:"Persienne / Cover",f_window_sensor:"Vinduessensor (valgfrit)",
  f_win_open:"Vinduestilstand 'åben'",f_win_tilt:"Vinduestilstand 'vippet'",f_win_tilt_none:"Deaktiveret",
  f_pos_win_open:"Position ved åbent vindue",f_pos_win_tilt:"Position ved vippet vindue",
  f_lock:"Låsebeskyttelse",f_min_pos:"Minimumposition ved åben dør",
  f_area_up:"Område (Op)",f_area_down:"Område (Ned)",
  f_pos_open:"Position Åben",f_pos_closed:"Position Lukket",f_pos_sun:"Solbeskyttelsesposition",
  f_drive_after:"Indhent hvis vindue åbent",f_drive_after_hint:"Handlingen udføres, så snart vinduet lukkes.",
  pick_entity:"Vælg entitet…",confirm_del_area:"Slet område \"{id}\"?",confirm_del_shutter:"Slet persienne?",
},
sv:{
  tab_dashboard:"Dashboard",tab_areas:"Områden",tab_shutters:"Persienner",
  subtitle:"{a} områden, {s} persienner",loading:"Laddar…",
  mode_time:"Tid",mode_brightness:"Ljusstyrka",mode_sun:"Solposition",
  shutter_s:"persienn",no_shutters:"Inga persienner",auto:"Automatik",
  btn_up:"Upp",btn_stop:"Stopp",btn_down:"Ner",btn_sun:"Solskydd",
  btn_add:"Lägg till",btn_save:"Spara",btn_cancel:"Avbryt",
  empty_areas:"Inga områden konfigurerade. Byt till fliken \"Områden\".",
  empty_areas_list:"Inga områden skapade ännu.",empty_shutters_list:"Inga persienner skapade ännu.",
  add_area:"Lägg till område",edit_area:"Redigera område",add_shutter:"Lägg till persienn",edit_shutter:"Redigera persienn",
  col_name:"Namn",col_id:"ID",col_mode:"Läge",col_shutters:"Persienner",
  col_cover:"Cover-entitet",col_area_up:"Område Upp",col_area_down:"Område Ner",col_window:"Fönster",
  f_name:"Namn",f_mode:"Styrläge",f_drive_delay:"Fördröjning mellan persienner (sek.)",
  f_sun_protect:"Aktivera solskydd",f_elev_thresh:"Elevationströskel (°)",
  f_light_entity:"Lampa/kontakt vid stängning (valfritt)",f_light_brightness:"Lampa ljusstyrka (%)",
  f_time_up:"Vardag upp",f_time_down:"Vardag ner",
  f_time_we_up:"Helg upp",f_time_we_down:"Helg ner",
  f_sunrise_off:"Soluppgång offset (min.)",f_sunset_off:"Solnedgång offset (min.)",
  sun_next_rise:"Nästa soluppgång",sun_next_set:"Nästa solnedgång",
  sun_trigger_up:"Upp kl.",sun_trigger_down:"Ner kl.",
  sun_elevation:"Aktuell elevation",sun_offset:"Offset",
  f_brightness_sensor:"Ljussensor",f_lux_up:"Lux upp-tröskel",f_lux_down:"Lux ner-tröskel",
  f_w_up_from:"Vardag upp från",f_w_up_to:"Vardag upp till",f_w_down_from:"Vardag ner från",f_w_down_to:"Vardag ner till",
  f_we_up_from:"Helg upp från",f_we_up_to:"Helg upp till",f_we_down_from:"Helg ner från",f_we_down_to:"Helg ner till",
  f_cover:"Persienn / Cover",f_window_sensor:"Fönstersensor (valfritt)",
  f_win_open:"Fönsterstatus 'öppet'",f_win_tilt:"Fönsterstatus 'vippat'",f_win_tilt_none:"Inaktiverad",
  f_pos_win_open:"Position vid öppet fönster",f_pos_win_tilt:"Position vid vippat fönster",
  f_lock:"Utelåsningsskydd",f_min_pos:"Minimiposition vid öppen dörr",
  f_area_up:"Område (Upp)",f_area_down:"Område (Ner)",
  f_pos_open:"Position Öppen",f_pos_closed:"Position Stängd",f_pos_sun:"Solskyddsposition",
  f_drive_after:"Hämta om fönster öppet",f_drive_after_hint:"Åtgärden utförs så snart fönstret stängs.",
  pick_entity:"Välj entitet…",confirm_del_area:"Ta bort område \"{id}\"?",confirm_del_shutter:"Ta bort persienn?",
},
pl:{
  tab_dashboard:"Panel",tab_areas:"Strefy",tab_shutters:"Rolety",
  subtitle:"{a} stref, {s} rolet",loading:"Ładowanie…",
  mode_time:"Czas",mode_brightness:"Jasność",mode_sun:"Pozycja słońca",
  shutter_s:"roleta",no_shutters:"Brak rolet",auto:"Automatyka",
  btn_up:"W górę",btn_stop:"Stop",btn_down:"W dół",btn_sun:"Osłona słoneczna",
  btn_add:"Dodaj",btn_save:"Zapisz",btn_cancel:"Anuluj",
  empty_areas:"Brak skonfigurowanych stref. Przejdź do zakładki \"Strefy\".",
  empty_areas_list:"Nie utworzono jeszcze żadnych stref.",empty_shutters_list:"Nie utworzono jeszcze żadnych rolet.",
  add_area:"Dodaj strefę",edit_area:"Edytuj strefę",add_shutter:"Dodaj roletę",edit_shutter:"Edytuj roletę",
  col_name:"Nazwa",col_id:"ID",col_mode:"Tryb",col_shutters:"Rolety",
  col_cover:"Encja cover",col_area_up:"Strefa W górę",col_area_down:"Strefa W dół",col_window:"Okno",
  f_name:"Nazwa",f_mode:"Tryb sterowania",f_drive_delay:"Opóźnienie między roletami (sek.)",
  f_sun_protect:"Włącz osłonę słoneczną",f_elev_thresh:"Próg elewacji (°)",
  f_light_entity:"Lampa/przełącznik przy zamykaniu (opcjonalnie)",f_light_brightness:"Jasność lampy (%)",
  f_time_up:"Dzień roboczy w górę",f_time_down:"Dzień roboczy w dół",
  f_time_we_up:"Weekend w górę",f_time_we_down:"Weekend w dół",
  f_sunrise_off:"Offset wschodu (min.)",f_sunset_off:"Offset zachodu (min.)",
  sun_next_rise:"Następny wschód",sun_next_set:"Następny zachód",
  sun_trigger_up:"W górę o",sun_trigger_down:"W dół o",
  sun_elevation:"Aktualna elewacja",sun_offset:"Offset",
  f_brightness_sensor:"Czujnik jasności",f_lux_up:"Próg lux w górę",f_lux_down:"Próg lux w dół",
  f_w_up_from:"Dzień roboczy góra od",f_w_up_to:"Dzień roboczy góra do",f_w_down_from:"Dzień roboczy dół od",f_w_down_to:"Dzień roboczy dół do",
  f_we_up_from:"Weekend góra od",f_we_up_to:"Weekend góra do",f_we_down_from:"Weekend dół od",f_we_down_to:"Weekend dół do",
  f_cover:"Roleta / Cover",f_window_sensor:"Czujnik okna (opcjonalnie)",
  f_win_open:"Stan okna 'otwarte'",f_win_tilt:"Stan okna 'uchylone'",f_win_tilt_none:"Wyłączone",
  f_pos_win_open:"Pozycja przy otwartym oknie",f_pos_win_tilt:"Pozycja przy uchylonym oknie",
  f_lock:"Blokada bezpieczeństwa",f_min_pos:"Minimalna pozycja przy otwartych drzwiach",
  f_area_up:"Strefa (W górę)",f_area_down:"Strefa (W dół)",
  f_pos_open:"Pozycja Otwarta",f_pos_closed:"Pozycja Zamknięta",f_pos_sun:"Pozycja osłony słonecznej",
  f_drive_after:"Nadrobić gdy okno otwarte",f_drive_after_hint:"Akcja zostanie wykonana po zamknięciu okna.",
  pick_entity:"Wybierz encję…",confirm_del_area:"Usunąć strefę \"{id}\"?",confirm_del_shutter:"Usunąć roletę?",
},
pt:{
  tab_dashboard:"Painel",tab_areas:"Zonas",tab_shutters:"Estores",
  subtitle:"{a} zonas, {s} estores",loading:"A carregar…",
  mode_time:"Horário",mode_brightness:"Luminosidade",mode_sun:"Posição solar",
  shutter_s:"estore",no_shutters:"Sem estores",auto:"Automático",
  btn_up:"Subir",btn_stop:"Parar",btn_down:"Descer",btn_sun:"Proteção solar",
  btn_add:"Adicionar",btn_save:"Guardar",btn_cancel:"Cancelar",
  empty_areas:"Nenhuma zona configurada. Mude para o separador \"Zonas\".",
  empty_areas_list:"Nenhuma zona criada.",empty_shutters_list:"Nenhum estore criado.",
  add_area:"Adicionar zona",edit_area:"Editar zona",add_shutter:"Adicionar estore",edit_shutter:"Editar estore",
  col_name:"Nome",col_id:"ID",col_mode:"Modo",col_shutters:"Estores",
  col_cover:"Entidade cover",col_area_up:"Zona Subir",col_area_down:"Zona Descer",col_window:"Janela",
  f_name:"Nome",f_mode:"Modo de controlo",f_drive_delay:"Atraso entre estores (seg.)",
  f_sun_protect:"Ativar proteção solar",f_elev_thresh:"Limiar de elevação (°)",
  f_light_entity:"Luz/interruptor ao fechar (opcional)",f_light_brightness:"Luminosidade da luz (%)",
  f_time_up:"Semana subir",f_time_down:"Semana descer",
  f_time_we_up:"Fim-de-semana subir",f_time_we_down:"Fim-de-semana descer",
  f_sunrise_off:"Offset nascer do sol (min.)",f_sunset_off:"Offset pôr do sol (min.)",
  sun_next_rise:"Próximo nascer do sol",sun_next_set:"Próximo pôr do sol",
  sun_trigger_up:"Subir às",sun_trigger_down:"Descer às",
  sun_elevation:"Elevação atual",sun_offset:"Offset",
  f_brightness_sensor:"Sensor de luminosidade",f_lux_up:"Limiar lux subir",f_lux_down:"Limiar lux descer",
  f_w_up_from:"Semana subir de",f_w_up_to:"Semana subir até",f_w_down_from:"Semana descer de",f_w_down_to:"Semana descer até",
  f_we_up_from:"Fim-de-semana subir de",f_we_up_to:"Fim-de-semana subir até",f_we_down_from:"Fim-de-semana descer de",f_we_down_to:"Fim-de-semana descer até",
  f_cover:"Estore / Cover",f_window_sensor:"Sensor de janela (opcional)",
  f_win_open:"Estado janela 'aberta'",f_win_tilt:"Estado janela 'basculante'",f_win_tilt_none:"Desativado",
  f_pos_win_open:"Posição janela aberta",f_pos_win_tilt:"Posição janela basculante",
  f_lock:"Proteção anti-bloqueio",f_min_pos:"Posição mín. porta aberta",
  f_area_up:"Zona (Subir)",f_area_down:"Zona (Descer)",
  f_pos_open:"Posição Aberta",f_pos_closed:"Posição Fechada",f_pos_sun:"Posição proteção solar",
  f_drive_after:"Recuperar se janela aberta",f_drive_after_hint:"A ação será executada assim que a janela for fechada.",
  pick_entity:"Selecionar entidade…",confirm_del_area:"Eliminar zona \"{id}\"?",confirm_del_shutter:"Eliminar estore?",
},
nb:{
  tab_dashboard:"Dashboard",tab_areas:"Områder",tab_shutters:"Persienner",
  subtitle:"{a} områder, {s} persienner",loading:"Laster…",
  mode_time:"Tid",mode_brightness:"Lysstyrke",mode_sun:"Solposisjon",
  shutter_s:"persienne",no_shutters:"Ingen persienner",auto:"Automatikk",
  btn_up:"Opp",btn_stop:"Stopp",btn_down:"Ned",btn_sun:"Solbeskyttelse",
  btn_add:"Legg til",btn_save:"Lagre",btn_cancel:"Avbryt",
  empty_areas:"Ingen områder konfigurert. Bytt til fanen \"Områder\".",
  empty_areas_list:"Ingen områder opprettet ennå.",empty_shutters_list:"Ingen persienner opprettet ennå.",
  add_area:"Legg til område",edit_area:"Rediger område",add_shutter:"Legg til persienne",edit_shutter:"Rediger persienne",
  col_name:"Navn",col_id:"ID",col_mode:"Modus",col_shutters:"Persienner",
  col_cover:"Cover-entitet",col_area_up:"Område Opp",col_area_down:"Område Ned",col_window:"Vindu",
  f_name:"Navn",f_mode:"Styringsmodus",f_drive_delay:"Forsinkelse mellom persienner (sek.)",
  f_sun_protect:"Aktiver solbeskyttelse",f_elev_thresh:"Elevasjonsterskel (°)",
  f_light_entity:"Lampe/bryter ved lukking (valgfritt)",f_light_brightness:"Lampe lysstyrke (%)",
  f_time_up:"Hverdag opp",f_time_down:"Hverdag ned",
  f_time_we_up:"Helg opp",f_time_we_down:"Helg ned",
  f_sunrise_off:"Soloppgang offset (min.)",f_sunset_off:"Solnedgang offset (min.)",
  sun_next_rise:"Neste soloppgang",sun_next_set:"Neste solnedgang",
  sun_trigger_up:"Opp kl.",sun_trigger_down:"Ned kl.",
  sun_elevation:"Gjeldende elevasjon",sun_offset:"Offset",
  f_brightness_sensor:"Lyssensor",f_lux_up:"Lux opp-terskel",f_lux_down:"Lux ned-terskel",
  f_w_up_from:"Hverdag opp fra",f_w_up_to:"Hverdag opp til",f_w_down_from:"Hverdag ned fra",f_w_down_to:"Hverdag ned til",
  f_we_up_from:"Helg opp fra",f_we_up_to:"Helg opp til",f_we_down_from:"Helg ned fra",f_we_down_to:"Helg ned til",
  f_cover:"Persienne / Cover",f_window_sensor:"Vindussensor (valgfritt)",
  f_win_open:"Vindustilstand 'åpent'",f_win_tilt:"Vindustilstand 'vippet'",f_win_tilt_none:"Deaktivert",
  f_pos_win_open:"Posisjon ved åpent vindu",f_pos_win_tilt:"Posisjon ved vippet vindu",
  f_lock:"Utestengingsbeskyttelse",f_min_pos:"Minimumsposisjon ved åpen dør",
  f_area_up:"Område (Opp)",f_area_down:"Område (Ned)",
  f_pos_open:"Posisjon Åpen",f_pos_closed:"Posisjon Lukket",f_pos_sun:"Solbeskyttelsesposisjon",
  f_drive_after:"Ta igjen hvis vindu åpent",f_drive_after_hint:"Handlingen utføres så snart vinduet lukkes.",
  pick_entity:"Velg entitet…",confirm_del_area:"Slette område \"{id}\"?",confirm_del_shutter:"Slette persienne?",
},
};

class ShutterPilotPanel extends LitElement {
  static get properties(){return{hass:{type:Object},narrow:{type:Boolean},panel:{type:Object},_tab:{attribute:false},_data:{attribute:false},_editArea:{attribute:false},_editShutter:{attribute:false}};}
  static get styles(){return css`
    :host{display:block;padding:16px;font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif);--sp:var(--primary-color,#03a9f4);--card-bg:var(--card-background-color,#1c1c1c);--txt:var(--primary-text-color);--txt2:var(--secondary-text-color);--divider:var(--divider-color,#333)}
    .topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px}
    .topbar h1{margin:0;font-size:24px;font-weight:500;color:var(--txt)}
    .topbar .sub{font-size:14px;color:var(--txt2)}
    .tabs{display:flex;gap:0;border-bottom:2px solid var(--divider);margin-bottom:20px}
    .tab{padding:10px 20px;cursor:pointer;font-size:14px;font-weight:500;color:var(--txt2);border-bottom:3px solid transparent;transition:all .2s}
    .tab:hover{color:var(--txt)}
    .tab.active{color:var(--sp);border-bottom-color:var(--sp)}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
    .card{background:var(--card-bg);border-radius:12px;padding:20px;box-shadow:var(--ha-card-box-shadow,0 2px 6px rgba(0,0,0,.15))}
    .card-hdr{display:flex;align-items:center;gap:12px;margin-bottom:16px}
    .card-hdr .ic{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--sp);color:#fff;--mdc-icon-size:22px}
    .card-hdr .info h2{margin:0;font-size:18px;font-weight:500;color:var(--txt)}
    .card-hdr .info span{font-size:13px;color:var(--txt2)}
    .auto-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--divider)}
    .auto-row .lbl{font-size:14px;color:var(--txt)}
    .srow{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--divider)}
    .srow:last-child{border-bottom:none}
    .srow .nm{font-size:14px;color:var(--txt);flex:1}
    .srow .pos{font-size:13px;color:var(--txt2);min-width:50px;text-align:right}
    .actions{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
    .btn{border:none;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer;font-weight:500;transition:opacity .2s;display:inline-flex;align-items:center;gap:6px}
    .btn:hover{opacity:.85}
    .btn.open{background:#4caf50;color:#fff} .btn.stop{background:#757575;color:#fff}
    .btn.close{background:#f44336;color:#fff}
    .btn.sun{background:#ff9800;color:#fff} .btn.add{background:var(--sp);color:#fff}
    .btn.edit{background:#607d8b;color:#fff} .btn.del{background:#e53935;color:#fff}
    .btn.cancel{background:var(--divider);color:var(--txt)} .btn.save{background:#4caf50;color:#fff}
    .empty{text-align:center;padding:48px 16px;color:var(--txt2)}
    table{width:100%;border-collapse:collapse;font-size:14px}
    th{text-align:left;padding:10px 8px;color:var(--txt2);font-weight:500;border-bottom:2px solid var(--divider)}
    td{padding:10px 8px;border-bottom:1px solid var(--divider);color:var(--txt)}
    tr:hover td{background:rgba(255,255,255,.03)}
    .form{background:var(--card-bg);border-radius:12px;padding:24px;margin-bottom:20px;max-width:600px}
    .form h3{margin:0 0 16px;font-size:18px;color:var(--txt)}
    .field{margin-bottom:14px}
    .field label{display:block;font-size:13px;color:var(--txt2);margin-bottom:4px}
    .field input,.field select{width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--divider);background:var(--primary-background-color,#111);color:var(--txt);font-size:14px;box-sizing:border-box}
    .field input[type=time]{cursor:pointer}
    .field select{appearance:auto}
    .field input:focus,.field select:focus{outline:none;border-color:var(--sp)}
    .field .hint{font-size:11px;color:var(--txt2);margin-top:2px}
    .slider-row{display:flex;align-items:center;gap:12px}
    .slider-row input[type=range]{flex:1;accent-color:var(--sp);height:6px;cursor:pointer}
    .slider-row .slider-val{min-width:44px;text-align:center;font-size:14px;font-weight:500;color:var(--sp)}
    .form-actions{display:flex;gap:8px;margin-top:16px}
    .chip{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:500}
    .chip.time{background:#1565c0;color:#fff} .chip.brightness{background:#f57f17;color:#fff} .chip.sun{background:#e65100;color:#fff}
    .sun-info{margin:12px 0 4px;padding:10px 12px;background:rgba(255,152,0,.08);border-radius:8px;border-left:3px solid #ff9800}
    .sun-row{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:13px;color:var(--txt);flex-wrap:wrap}
    .sun-row ha-icon{--mdc-icon-size:18px;color:#ff9800;flex-shrink:0}
    .sun-off{font-size:12px;color:var(--txt2)}
  `;}

  constructor(){super();this._tab="dashboard";this._data=null;this._editArea=null;this._editShutter=null;}
  connectedCallback(){super.connectedCallback?.();this._load();}
  updated(c){if(c.has("hass")&&this.hass&&!this._data)this._load();}

  get _lang(){const l=(this.hass?.language||"en").substring(0,2);return I18N[l]?l:"en";}
  t(k){return(I18N[this._lang]||I18N.en)[k]||k;}
  _modeName(m){return this.t("mode_"+m)||m;}

  async _load(){if(!this.hass)return;try{this._data=await this.hass.callWS({type:"shutter_pilot/get_status"});}catch(e){console.warn("SP load",e);}}
  _entities(domains){if(!this.hass?.states)return[];return Object.keys(this.hass.states).filter(e=>domains.some(d=>e.startsWith(d+"."))).sort();}

  render(){
    const d=this._data;const T=k=>this.t(k);
    return html`
      <div class="topbar"><div><h1>Shutter Pilot</h1>
        ${d?html`<div class="sub">${T("subtitle").replace("{a}",d.areas?.length||0).replace("{s}",d.shutters?.length||0)}</div>`:""}</div></div>
      <div class="tabs">
        ${["dashboard","areas","shutters"].map(t=>html`
          <div class="tab ${this._tab===t?"active":""}" @click=${()=>{this._tab=t;this._editArea=null;this._editShutter=null;this.requestUpdate();}}>
            ${T("tab_"+t)}</div>`)}
      </div>
      ${!d?html`<div class="empty">${T("loading")}</div>`:
        this._tab==="dashboard"?this._renderDashboard(d):
        this._tab==="areas"?this._renderAreas(d):
        this._renderShutters(d)}`;
  }

  /* ─── Dashboard ─── */
  _renderDashboard(d){
    if(!d.areas?.length)return html`<div class="empty"><ha-icon icon="mdi:window-shutter-settings"></ha-icon><p>${this.t("empty_areas")}</p></div>`;
    return html`<div class="grid">${d.areas.map(a=>this._dashCard(a,d))}</div>`;
  }
  _dashCard(area,d){
    const id=area.id||"",name=area.name||id,mode=area.mode||"time";
    const sh=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id);
    const autoOn=d.auto_modes?.[id]!==false;
    return html`<div class="card">
      <div class="card-hdr"><div class="ic"><ha-icon icon="${MODE_ICONS[mode]||"mdi:blinds"}"></ha-icon></div>
        <div class="info"><h2>${name}</h2><span>${this._modeName(mode)} · ${sh.length} ${this.t("shutter_s")}</span></div></div>
      <div class="auto-row"><span class="lbl">${this.t("auto")}</span>
        <ha-switch .checked=${autoOn} @change=${e=>this._toggleAuto(id,e.target.checked)}></ha-switch></div>
      ${mode==="sun"?this._renderSunInfo(area,d):""}
      <div style="margin-top:8px">${sh.length===0?html`<div style="padding:8px 0;color:var(--txt2);font-size:13px">${this.t("no_shutters")}</div>`:
        sh.map(s=>{const st=this.hass?.states?.[s.cover_entity_id];const p=st?.attributes?.current_position;
          return html`<div class="srow"><span class="nm">${st?.attributes?.friendly_name||s.name||s.cover_entity_id}</span><span class="pos">${p!=null?Math.round(p)+"%":"–"}</span></div>`;})}</div>
      <div class="actions">
        <button class="btn open" @click=${()=>this._coverAction(sh,"open")}><ha-icon icon="mdi:arrow-up-bold"></ha-icon>${this.t("btn_up")}</button>
        <button class="btn stop" @click=${()=>this._coverAction(sh,"stop")}><ha-icon icon="mdi:stop"></ha-icon>${this.t("btn_stop")}</button>
        <button class="btn close" @click=${()=>this._coverAction(sh,"close")}><ha-icon icon="mdi:arrow-down-bold"></ha-icon>${this.t("btn_down")}</button>
        <button class="btn sun" @click=${()=>this._coverAction(sh,"sun")}><ha-icon icon="mdi:sun-wireless-outline"></ha-icon>${this.t("btn_sun")}</button>
      </div></div>`;
  }
  _renderSunInfo(area,d){
    const sun=d.sun||{};
    const offUp=parseInt(area.sunrise_offset)||0;
    const offDown=parseInt(area.sunset_offset)||0;
    const fmtTime=(iso,offsetMin)=>{
      if(!iso)return "–";
      try{const dt=new Date(iso);dt.setMinutes(dt.getMinutes()+offsetMin);return dt.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});}catch(e){return "–";}
    };
    const fmtRaw=(iso)=>{
      if(!iso)return "–";
      try{return new Date(iso).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});}catch(e){return "–";}
    };
    const elev=sun.elevation!=null?sun.elevation.toFixed(1)+"°":"–";
    return html`<div class="sun-info">
      <div class="sun-row"><ha-icon icon="mdi:weather-sunset-up"></ha-icon>
        <span>${this.t("sun_next_rise")}: <b>${fmtRaw(sun.next_rising)}</b></span>
        ${offUp?html`<span class="sun-off">(${this.t("sun_offset")}: ${offUp>0?"+":""}${offUp} min → ${this.t("sun_trigger_up")} <b>${fmtTime(sun.next_rising,offUp)}</b>)</span>`:
          html`<span class="sun-off">(${this.t("sun_trigger_up")} <b>${fmtRaw(sun.next_rising)}</b>)</span>`}</div>
      <div class="sun-row"><ha-icon icon="mdi:weather-sunset-down"></ha-icon>
        <span>${this.t("sun_next_set")}: <b>${fmtRaw(sun.next_setting)}</b></span>
        ${offDown?html`<span class="sun-off">(${this.t("sun_offset")}: ${offDown>0?"+":""}${offDown} min → ${this.t("sun_trigger_down")} <b>${fmtTime(sun.next_setting,offDown)}</b>)</span>`:
          html`<span class="sun-off">(${this.t("sun_trigger_down")} <b>${fmtRaw(sun.next_setting)}</b>)</span>`}</div>
      <div class="sun-row"><ha-icon icon="mdi:angle-acute"></ha-icon>
        <span>${this.t("sun_elevation")}: <b>${elev}</b></span></div>
    </div>`;
  }

  /* ─── Areas Tab ─── */
  _renderAreas(d){
    if(this._editArea)return this._renderAreaForm(d);
    return html`
      <div style="margin-bottom:16px"><button class="btn add" @click=${()=>{this._editArea={id:"",name:"",mode:"time",drive_delay:10,sun_protect_enabled:false,elevation_threshold:4,down_light_entity:"",down_light_brightness:40,time_up:"07:00",time_down:"19:00",time_we_up:"08:00",time_we_down:"20:00",sunrise_offset:0,sunset_offset:0,brightness_sensor:"",lux_down:400,lux_up:500,w_up_from:"05:00",w_up_to:"09:00",w_down_from:"16:00",w_down_to:"23:59",we_up_from:"07:00",we_up_to:"10:00",we_down_from:"16:00",we_down_to:"23:59",_isNew:true};this.requestUpdate();}}><ha-icon icon="mdi:plus"></ha-icon>${this.t("add_area")}</button></div>
      ${!d.areas?.length?html`<div class="empty">${this.t("empty_areas_list")}</div>`:html`
      <div class="card"><table>
        <tr><th>${this.t("col_name")}</th><th>${this.t("col_id")}</th><th>${this.t("col_mode")}</th><th>${this.t("col_shutters")}</th><th></th></tr>
        ${d.areas.map(a=>{const id=a.id||"";const cnt=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id).length;
          return html`<tr>
            <td><strong>${a.name||id}</strong></td><td style="color:var(--txt2)">${id}</td>
            <td><span class="chip ${a.mode||"time"}">${this._modeName(a.mode)}</span></td>
            <td>${cnt}</td>
            <td style="text-align:right">
              <button class="btn edit" @click=${()=>{this._editArea={...a,_isNew:false};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
              <button class="btn del" @click=${()=>this._deleteArea(id)}><ha-icon icon="mdi:delete"></ha-icon></button></td></tr>`;})}
      </table></div>`}`;
  }
  _renderAreaForm(){
    const a=this._editArea;const m=a.mode||"time";const T=k=>this.t(k);
    const f=(k,lbl,type="text")=>html`<div class="field"><label>${lbl}</label><input type="${type}" .value=${a[k]??""}  @input=${e=>{a[k]=type==="number"?Number(e.target.value):e.target.value;this.requestUpdate();}}></div>`;
    const tm=(k,lbl)=>html`<div class="field"><label>${lbl}</label><input type="time" .value=${a[k]||"07:00"} @input=${e=>{a[k]=e.target.value;this.requestUpdate();}}></div>`;
    const ep=(k,lbl,domains)=>{const lid=`dl_${k}`;const ents=this._entities(domains);return html`<div class="field"><label>${lbl}</label>
      <input list="${lid}" .value=${a[k]||""} @input=${e=>{a[k]=e.target.value;this.requestUpdate();}} placeholder="${T("pick_entity")}">
      <datalist id="${lid}">${ents.map(e=>html`<option value="${e}">${this.hass.states[e]?.attributes?.friendly_name||e}</option>`)}</datalist></div>`;};
    return html`<div class="form"><h3>${a._isNew?T("add_area"):T("edit_area")}</h3>
      ${f("name",T("f_name"))}
      ${a._isNew?"":html`<div class="field"><label>${T("col_id")}</label><input disabled .value=${a.id}></div>`}
      <div class="field"><label>${T("f_mode")}</label>
        <select .value=${m} @change=${e=>{a.mode=e.target.value;this.requestUpdate();}}>
          <option value="time" ?selected=${m==="time"}>${T("mode_time")}</option>
          <option value="brightness" ?selected=${m==="brightness"}>${T("mode_brightness")}</option>
          <option value="sun" ?selected=${m==="sun"}>${T("mode_sun")}</option></select></div>
      ${f("drive_delay",T("f_drive_delay"),"number")}
      <div class="field"><label><input type="checkbox" .checked=${!!a.sun_protect_enabled} @change=${e=>{a.sun_protect_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_sun_protect")}</label></div>
      ${a.sun_protect_enabled?f("elevation_threshold",T("f_elev_thresh"),"number"):""}
      ${ep("down_light_entity",T("f_light_entity"),["light","switch"])}
      ${f("down_light_brightness",T("f_light_brightness"),"number")}
      ${m==="time"?html`${tm("time_up",T("f_time_up"))}${tm("time_down",T("f_time_down"))}${tm("time_we_up",T("f_time_we_up"))}${tm("time_we_down",T("f_time_we_down"))}`:
        m==="sun"?html`${f("sunrise_offset",T("f_sunrise_off"),"number")}${f("sunset_offset",T("f_sunset_off"),"number")}`:
        html`${ep("brightness_sensor",T("f_brightness_sensor"),["sensor"])}${f("lux_up",T("f_lux_up"),"number")}${f("lux_down",T("f_lux_down"),"number")}
          ${tm("w_up_from",T("f_w_up_from"))}${tm("w_up_to",T("f_w_up_to"))}${tm("w_down_from",T("f_w_down_from"))}${tm("w_down_to",T("f_w_down_to"))}
          ${tm("we_up_from",T("f_we_up_from"))}${tm("we_up_to",T("f_we_up_to"))}${tm("we_down_from",T("f_we_down_from"))}${tm("we_down_to",T("f_we_down_to"))}`}
      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveArea()}><ha-icon icon="mdi:content-save"></ha-icon>${T("btn_save")}</button>
        <button class="btn cancel" @click=${()=>{this._editArea=null;this.requestUpdate();}}>${T("btn_cancel")}</button></div></div>`;
  }

  /* ─── Shutters Tab ─── */
  _renderShutters(d){
    if(this._editShutter)return this._renderShutterForm(d);
    const areaName=id=>{const a=d.areas.find(x=>x.id===id);return a?a.name:id;};const T=k=>this.t(k);
    return html`
      <div style="margin-bottom:16px"><button class="btn add" @click=${()=>{this._editShutter={cover_entity_id:"",name:"",window_entity_id:"",window_open_state:"on",window_tilted_state:"none",position_when_window_open:100,position_when_window_tilted:50,lock_protection:false,min_position_when_open:20,area_up_id:d.areas[0]?.id||"",area_down_id:d.areas[0]?.id||"",position_open:100,position_closed:0,position_sun_protect:50,drive_after_close:false,_isNew:true,_index:null};this.requestUpdate();}}><ha-icon icon="mdi:plus"></ha-icon>${T("add_shutter")}</button></div>
      ${!d.shutters?.length?html`<div class="empty">${T("empty_shutters_list")}</div>`:html`
      <div class="card"><table>
        <tr><th>${T("col_name")}</th><th>${T("col_cover")}</th><th>${T("col_area_up")}</th><th>${T("col_area_down")}</th><th>${T("col_window")}</th><th></th></tr>
        ${d.shutters.map((s,i)=>{const st=this.hass?.states?.[s.cover_entity_id];
          return html`<tr>
            <td><strong>${s.name||"–"}</strong></td>
            <td style="color:var(--txt2)">${st?.attributes?.friendly_name||s.cover_entity_id}</td>
            <td>${areaName(s.area_up_id)}</td><td>${areaName(s.area_down_id)}</td>
            <td>${s.window_entity_id||"–"}</td>
            <td style="text-align:right">
              <button class="btn edit" @click=${()=>{this._editShutter={...s,_isNew:false,_index:i};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
              <button class="btn del" @click=${()=>this._deleteShutter(i)}><ha-icon icon="mdi:delete"></ha-icon></button></td></tr>`;})}
      </table></div>`}`;
  }
  _renderShutterForm(d){
    const s=this._editShutter;const areas=d.areas||[];const T=k=>this.t(k);
    const f=(k,lbl,type="text")=>html`<div class="field"><label>${lbl}</label><input type="${type}" .value=${s[k]??""}  @input=${e=>{s[k]=type==="number"?Number(e.target.value):e.target.value;this.requestUpdate();}}></div>`;
    const pct=(k,lbl)=>html`<div class="field"><label>${lbl}</label><div class="slider-row">
      <input type="range" min="0" max="100" .value=${s[k]??0} @input=${e=>{s[k]=Number(e.target.value);this.requestUpdate();}}>
      <span class="slider-val">${s[k]??0}%</span></div></div>`;
    const ep=(k,lbl,domains)=>{const lid=`dl_s_${k}`;const ents=this._entities(domains);return html`<div class="field"><label>${lbl}</label>
      <input list="${lid}" .value=${s[k]||""} @input=${e=>{s[k]=e.target.value;this.requestUpdate();}} placeholder="${T("pick_entity")}">
      <datalist id="${lid}">${ents.map(e=>html`<option value="${e}">${this.hass.states[e]?.attributes?.friendly_name||e}</option>`)}</datalist></div>`;};
    const sel=(k,lbl,opts)=>html`<div class="field"><label>${lbl}</label><select .value=${s[k]||""} @change=${e=>{s[k]=e.target.value;this.requestUpdate();}}>
      ${opts.map(o=>typeof o==="string"?html`<option value="${o}" ?selected=${s[k]===o}>${o}</option>`:html`<option value="${o.v}" ?selected=${s[k]===o.v}>${o.l}</option>`)}</select></div>`;
    const areaSel=(k,lbl)=>sel(k,lbl,areas.map(a=>({v:a.id,l:a.name||a.id})));
    return html`<div class="form"><h3>${s._isNew?T("add_shutter"):T("edit_shutter")}</h3>
      ${ep("cover_entity_id",T("f_cover"),["cover"])}
      ${f("name",T("f_name"))}
      ${ep("window_entity_id",T("f_window_sensor"),["binary_sensor","sensor"])}
      ${sel("window_open_state",T("f_win_open"),WIN_OPEN_OPTS)}
      ${sel("window_tilted_state",T("f_win_tilt"),
        [{v:"none",l:T("f_win_tilt_none")},...WIN_TILT_OPTS.filter(x=>x!=="none").map(x=>({v:x,l:x}))])}
      ${pct("position_when_window_open",T("f_pos_win_open"))}
      ${pct("position_when_window_tilted",T("f_pos_win_tilt"))}
      <div class="field"><label><input type="checkbox" .checked=${!!s.lock_protection} @change=${e=>{s.lock_protection=e.target.checked;this.requestUpdate();}}> ${T("f_lock")}</label></div>
      ${s.lock_protection?pct("min_position_when_open",T("f_min_pos")):""}
      ${areaSel("area_up_id",T("f_area_up"))}
      ${areaSel("area_down_id",T("f_area_down"))}
      ${pct("position_open",T("f_pos_open"))}
      ${pct("position_closed",T("f_pos_closed"))}
      ${pct("position_sun_protect",T("f_pos_sun"))}
      <div class="field"><label><input type="checkbox" .checked=${!!s.drive_after_close} @change=${e=>{s.drive_after_close=e.target.checked;this.requestUpdate();}}> ${T("f_drive_after")}</label>
        <div class="hint">${T("f_drive_after_hint")}</div></div>
      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveShutter()}><ha-icon icon="mdi:content-save"></ha-icon>${T("btn_save")}</button>
        <button class="btn cancel" @click=${()=>{this._editShutter=null;this.requestUpdate();}}>${T("btn_cancel")}</button></div></div>`;
  }

  /* ─── Actions ─── */
  async _toggleAuto(id,on){try{await this.hass.callWS({type:"shutter_pilot/set_auto_mode",area_id:id,enabled:on});await this._load();}catch(e){console.warn(e);}}
  _coverAction(shutters,action){
    const eids=shutters.map(s=>s.cover_entity_id).filter(Boolean);
    if(!eids.length)return;
    if(action==="open")this.hass.callService("cover","open_cover",{entity_id:eids});
    else if(action==="close")this.hass.callService("cover","close_cover",{entity_id:eids});
    else if(action==="stop")this.hass.callService("cover","stop_cover",{entity_id:eids});
    else if(action==="sun"){for(const s of shutters){const eid=s.cover_entity_id;const pos=s.position_sun_protect??50;if(eid)this.hass.callService("cover","set_cover_position",{entity_id:eid,position:pos});}}
  }
  async _saveArea(){
    const a={...this._editArea};delete a._isNew;delete a._index;
    if(!a.id){a.id=a.name.toLowerCase().replace(/[äÄ]/g,"ae").replace(/[öÖ]/g,"oe").replace(/[üÜ]/g,"ue").replace(/[ß]/g,"ss").replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,"")||"area";}
    try{await this.hass.callWS({type:"shutter_pilot/save_area",area:a});this._editArea=null;await this._load();}catch(e){console.warn(e);alert("Error: "+e.message);}
  }
  async _deleteArea(id){
    if(!confirm(this.t("confirm_del_area").replace("{id}",id)))return;
    try{await this.hass.callWS({type:"shutter_pilot/delete_area",area_id:id});await this._load();}catch(e){console.warn(e);}
  }
  async _saveShutter(){
    const s={...this._editShutter};const idx=s._index;delete s._isNew;delete s._index;
    try{await this.hass.callWS({type:"shutter_pilot/save_shutter",shutter:s,index:idx});this._editShutter=null;await this._load();}catch(e){console.warn(e);alert("Error: "+e.message);}
  }
  async _deleteShutter(idx){
    if(!confirm(this.t("confirm_del_shutter")))return;
    try{await this.hass.callWS({type:"shutter_pilot/delete_shutter",index:idx});await this._load();}catch(e){console.warn(e);}
  }
}
customElements.define("shutter-pilot-panel",ShutterPilotPanel);
