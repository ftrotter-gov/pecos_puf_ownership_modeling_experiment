################################################################################
#################### HOSPITAL OWNERSHIP HEIRARCHY TABLE ########################
################################################################################

#This script uses two monthly CMS files:
#1 Hospital enrollment file
#2 Hospital all owners file

#The script links both files using ENROLLMENT ID and creates the final
#hospital ownership heirarchy table using four sequential rules.

######## FILE LOCATIONS ########

data_dir = "/intake"

################################################################################
#August files are the defaults. Optional command-line arguments can supply a  #
#different enrollment filename and All Owners filename without editing code.  #
################################################################################
script_args = commandArgs(trailingOnly = TRUE)
script_args = script_args[script_args != "--args"]

enrollment_file = ifelse(
  length(script_args) >= 1,
  script_args[1],
  "Hospital_Enrollments_aug2026.csv"
)

allowners_file = ifelse(
  length(script_args) >= 2,
  script_args[2],
  "Hospital_All_Owners_aug2026.csv"
)


################################################################################
######################## STEP 1: LOAD AND LINK FILES ###########################
################################################################################
###Hospital enrollment data set###
hospital_enrollments = read.csv(
  file = file.path(data_dir, enrollment_file),
  header = TRUE,
  stringsAsFactors = FALSE,
  colClasses = "character"
)

###Hospital all owners data set###
hospital_allowners = read.csv(
  file = file.path(data_dir, allowners_file),
  header = TRUE,
  stringsAsFactors = FALSE,
  colClasses = "character"
)

#Convert CMS text from Windows encoding to UTF-8 for RStudio and Excel.
#The sub = "" option removes only invalid text bytes; it does not remove rows.
hospital_enrollments[] = lapply(
  hospital_enrollments,
  function(x) iconv(x, from = "windows-1252", to = "UTF-8", sub = "")
)

hospital_allowners[] = lapply(
  hospital_allowners,
  function(x) iconv(x, from = "windows-1252", to = "UTF-8", sub = "")
)

#Keep the enrollment variables needed for the heirarchy
hospital_enrollments = hospital_enrollments[,c(
  "ENROLLMENT.ID",
  "ASSOCIATE.ID",
  "ORGANIZATION.NAME",
  "CCN",
  "ORGANIZATION.TYPE.STRUCTURE",
  "ORGANIZATION.OTHER.TYPE.TEXT",
  "PROPRIETARY.NONPROFIT"
)]

#Keep the owner variables needed for the heirarchy
hospital_allowners = hospital_allowners[,c(
  "ENROLLMENT.ID",
  "ASSOCIATE.ID",
  "ORGANIZATION.NAME",
  "ASSOCIATE.ID...OWNER",
  "TYPE...OWNER",
  "ROLE.CODE...OWNER",
  "TITLE...OWNER"
)]

#Link the enrollment and all owners files using ENROLLMENT ID
owners_enrollments = merge(
  hospital_enrollments,
  hospital_allowners,
  by = "ENROLLMENT.ID",
  all.x = TRUE,
  sort = FALSE
)

#Confirm that ASSOCIATE ID and ORGANIZATION NAME agree after the merge.
#Some monthly files add a leading zero to ASSOCIATE ID, so leading zeros are
#removed for this comparison only. The original source values are preserved.
associate_id_enrollment = sub(
  "^0+",
  "",
  trimws(owners_enrollments$ASSOCIATE.ID.x)
)

associate_id_allowners = sub(
  "^0+",
  "",
  trimws(owners_enrollments$ASSOCIATE.ID.y)
)

associate_mismatch = associate_id_enrollment != associate_id_allowners &
  !is.na(owners_enrollments$ASSOCIATE.ID.y)

name_mismatch = toupper(trimws(owners_enrollments$ORGANIZATION.NAME.x)) !=
  toupper(trimws(owners_enrollments$ORGANIZATION.NAME.y)) &
  !is.na(owners_enrollments$ORGANIZATION.NAME.y)

stopifnot(sum(associate_mismatch, na.rm = TRUE) == 0)
stopifnot(sum(name_mismatch, na.rm = TRUE) == 0)

#Use the hospital information from the enrollment file
owners_enrollments$ASSOCIATE.ID = owners_enrollments$ASSOCIATE.ID.x
owners_enrollments$ORGANIZATION.NAME = owners_enrollments$ORGANIZATION.NAME.x

print(paste("Enrollment rows:", nrow(hospital_enrollments)))
print(paste("All owner rows:", nrow(hospital_allowners)))
print(paste("Linked rows:", nrow(owners_enrollments)))
print(paste("Enrollment file:", enrollment_file))
print(paste("All owners file:", allowners_file))


################################################################################
######################## STEP 2: PREPARE THE CCN FILE ###########################
################################################################################

#Clean CCN and add the leading zero to five-character CCNs
owners_enrollments$CCN = trimws(owners_enrollments$CCN)

owners_enrollments$CCN = ifelse(
  nchar(owners_enrollments$CCN) == 5,
  paste0("0", owners_enrollments$CCN),
  owners_enrollments$CCN
)

#Identify special-unit CCNs using the third character of the CCN
owners_enrollments$CCN.position.3 = substr(owners_enrollments$CCN, 3, 3)

owners_enrollments$special.unit = ifelse(
  owners_enrollments$CCN.position.3 %in% c("M","S"), "Psychiatric",
  ifelse(
    owners_enrollments$CCN.position.3 %in% c("R","T"), "Rehabilitation",
    ifelse(
      owners_enrollments$CCN.position.3 %in% c("U","W","Y","Z"), "Swing Bed",
      ""
    )
  )
)

#Save the excluded special-unit CCNs for review
ccn_exclusions = owners_enrollments[owners_enrollments$special.unit != "",c(
  "CCN",
  "CCN.position.3",
  "special.unit",
  "ORGANIZATION.NAME"
)]

ccn_exclusions = unique(ccn_exclusions)

#Keep only eligible hospital CCNs
hospital_data = owners_enrollments[
  owners_enrollments$CCN != "" & owners_enrollments$special.unit == "",
]

print(paste("Source CCNs:", length(unique(owners_enrollments$CCN))))
print(paste("Excluded CCNs:", length(unique(ccn_exclusions$CCN))))
print(paste("Eligible hospital CCNs:", length(unique(hospital_data$CCN))))


################################################################################
#################### STEP 3: APPLY THE FOUR HEIRARCHY RULES #####################
################################################################################

#Clean the text variables used in the four rules
hospital_data$structure = toupper(trimws(ifelse(
  is.na(hospital_data$ORGANIZATION.TYPE.STRUCTURE),
  "",
  hospital_data$ORGANIZATION.TYPE.STRUCTURE
)))

hospital_data$other.text = toupper(trimws(ifelse(
  is.na(hospital_data$ORGANIZATION.OTHER.TYPE.TEXT),
  "",
  hospital_data$ORGANIZATION.OTHER.TYPE.TEXT
)))

hospital_data$nonprofit = toupper(trimws(ifelse(
  is.na(hospital_data$PROPRIETARY.NONPROFIT),
  "",
  hospital_data$PROPRIETARY.NONPROFIT
)))

hospital_data$owner.type = toupper(trimws(ifelse(
  is.na(hospital_data$TYPE...OWNER),
  "",
  hospital_data$TYPE...OWNER
)))

hospital_data$owner.role = toupper(trimws(ifelse(
  is.na(hospital_data$ROLE.CODE...OWNER),
  "",
  hospital_data$ROLE.CODE...OWNER
)))

hospital_data$owner.title = toupper(trimws(ifelse(
  is.na(hospital_data$TITLE...OWNER),
  "",
  hospital_data$TITLE...OWNER
)))

#Terms used for partnership, government, and board-title evidence
partnership_terms = "\\b(PARTNERSHIP|LIMITED\\s+PARTNER|GENERAL\\s+PARTNER|LP|LLP)\\b|\\bL\\.P\\.\\b"

government_terms = paste0(
  "\\b(FEDERAL|COUNTY|CITY|MUNICIPAL|MUNICIPALITY|TOWNSHIP|PARISH|GOVERNMENT|",
  "GOVERNMENTAL|GOVT|GOVERMENT|GOVERMENTAL|GOVENMENTAL|GOVERNEMNT|PUBLIC|STATE|",
  "DISTRICT|AUTHORITY|TRIBAL|TRIBE|IHS|INDIAN\\s+HEALTH\\s+SERVICE|COMMONWEALTH|",
  "INSTRUMENTALITY|DEPARTMENT\\s+OF\\s+DEFENSE)\\b|POLITICAL\\s*SUB[ -]?",
  "(DIVISION|DIV|DIVISON)|POLITICALSUB"
)

board_terms = "\\bBOARD\\b|\\bTRUSTEES?\\b|\\bBOD\\b|\\bBOT\\b|\\bGOVERNING\\s+(BOARD|BODY)\\b"

#Rule 1: Any direct owner role code 34
hospital_data$rule1.has.owners = ifelse(
  hospital_data$owner.role == "34",
  1,
  0
)

#Rule 2: Partnership structure or reviewed partnership text
hospital_data$rule2.partnership = ifelse(
  hospital_data$structure == "PARTNERSHIP" |
    (hospital_data$structure == "OTHER" & grepl(partnership_terms, hospital_data$other.text, perl = TRUE)),
  1,
  0
)

#Rule 3: Government structure or reviewed government/public text
hospital_data$rule3.government = ifelse(
  hospital_data$structure == "GOVERNMENT" |
    (hospital_data$structure == "OTHER" & grepl(government_terms, hospital_data$other.text, perl = TRUE)),
  1,
  0
)

#Rule 4: Nonprofit code N and an individual owner with board-title text
hospital_data$nonprofit.N = ifelse(
  hospital_data$nonprofit == "N",
  1,
  0
)

hospital_data$board.title = ifelse(
  hospital_data$owner.type == "I" & grepl(board_terms, hospital_data$owner.title, perl = TRUE),
  1,
  0
)

#Create one row per hospital CCN with the maximum evidence flag for each rule
hospital_flags = aggregate(
  cbind(
    rule1.has.owners,
    rule2.partnership,
    rule3.government,
    nonprofit.N,
    board.title
  ) ~ CCN,
  data = hospital_data,
  FUN = max
)

#Add the hospital name for review
hospital_names = aggregate(
  ORGANIZATION.NAME ~ CCN,
  data = hospital_data,
  FUN = function(x) paste(sort(unique(x)), collapse = " | ")
)

hospital_flags = merge(
  hospital_names,
  hospital_flags,
  by = "CCN",
  all.x = TRUE,
  sort = FALSE
)

#Apply the four rules in order. The first match wins.
#Hospitals that do not meet rules 1-4 become Not categorized.
hospital_flags$final.category = ifelse(
  hospital_flags$rule1.has.owners == 1, "Has owners",
  ifelse(
    hospital_flags$rule2.partnership == 1, "Partnerships",
    ifelse(
      hospital_flags$rule3.government == 1, "Government",
      ifelse(
        hospital_flags$nonprofit.N == 1 & hospital_flags$board.title == 1,
        "Non-profit",
        "Not categorized"
      )
    )
  )
)


################################################################################
#################### STEP 4: CREATE THE HEIRARCHY TABLE #########################
################################################################################

category_order = c(
  "Has owners",
  "Partnerships",
  "Government",
  "Non-profit",
  "Not categorized"
)

category_count = table(factor(
  hospital_flags$final.category,
  levels = category_order
))

heirarchy_table = data.frame(
  Category = c("Hospitals, total", category_order),
  Count = c(nrow(hospital_flags), as.numeric(category_count)),
  Percent = c(1, as.numeric(category_count) / nrow(hospital_flags))
)

print(heirarchy_table)


