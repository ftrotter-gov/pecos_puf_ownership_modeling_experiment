cd "PECOS\Ownership data26/db_work26"
stop								hospitals
  
Because role 34 should never sum > 100%, sum of ownership % is an simple quality metric.
For max versability, includes both 34 (direct owner) & 35 (indirect owner).

  I. Retain only owners with most recent enr ID		[own_2roles_cur_oh]
  *A. Drop missing & save in order to merge back
			Current & historic owners: sum of 34%  
  *B. Find most recent enrollment ID (for each hosp)
   *1. Retain only most current effective date (for each hospital)
   *2. Create lookup file 
   *3. Retain enr_id (for that date)
  *C. Merge back into original file (w/o missing shr%)
			Current owners only; before de-dup: sum of 34%
  *D. Create file of 34-35 pairs to analyze
  *E. De-dup multiple enr_id 
  *F. Finalize hosp-owner file
			Current owners only: sum of 34%
 II. Distribution of sums of ownership shares (table)
III. Typical # of years between oldest and youngest effective dates
***************************

  I. Retain only owners with APPARENTLY most recent enr ID

  *A. For each hosp, keep only highest enr_id; then merge to full file
  
use early_steps/hosp/owner_2roles_h26, clear		//18,046 obs; 88 vars
  order assoc_id enr_id effect_dt_oh own_pct name_prov name_own owned_by_another  role_cd 
  drop if mi(own_pct)		//dropped 1,700;
  
  gsort assoc_id -enr_id 
  bys assoc_id: g index=_n
   keep if index==1			//12,925 dropped;  3,421 obs
  isid assoc_id 		//OK

merge 1:m assoc_id enr_id  using early_steps/hosp/owner_2roles_h26	

  keep if _merge==3		//6,120 dropped;  11,926 merged
  drop if mi(own_pct)	//0 dropped

  gsort assoc_id -enr_id 	//review data
    format %-10.0f assoc_id
	*  format %-10.0f assoc_id
  order role_cd, after(own_pct)
  drop effect_dt_oh index _merge
  
  
save early_steps/hosp/tmp/owner_2roles_h26, replace	//11,926  obs; 87 var;  34 & 35

***********

collapse (sum) own_pct, by (assoc_id role_cd)
keep if role_cd==34
 
 gsort -own_pct 
 
*******
			Current owners only; before de-dup: sum of 34%
			
use early_steps/hosp/tmp/both34_35, replace
  keep if role_cd==34
  keep if inlist(assoc_id,7719899947,5698071173,6103348479)		//11 obs
  order assoc_id dt_max_h effect_dt_oh 
  gsort enr_id enr_id 
collapse (sum) own_pct, by (assoc_id name_prov)
   gsort assoc_id
   order assoc_id own_pct
   
   First three hosp: same assoc_id, dt_max_h, effect_dt_oh, names of hosp & owner 
   for dif enr_id;
assoc_id	own_pct	name_prov
5698071173	600	MCHS HOSPITALS INC
6103348479	300	SAINT MARY OF NAZARETH HOSPITAL - CHICAGO LLC
7719899947	200	BOWLING GREEN-WARREN COUNTY COMMUNITY HOSPITAL CORPORATION


**************************************************************************

   *D. Create file of 34-35 pairs to analyze
   
use early_steps/hosp/tmp/owner_2roles_h26, clear		//11,926 obs
  drop enr_id
collapse cnt, by(assoc_id role_cd)
  
   *enr_id is no longer relevant
*collapse cnt, by(assoc_id assoc_id_owner) 				//3,421 obs

collapse cnt, by(assoc_id assoc_id_owner role_cd)	//3,421 obs; prov-owner-role
collapse cnt, by(assoc_id assoc_id_owner)		//3,421 obs
  keep if cnt==2								//0 obs
  
  order enr_id assoc_id name_prov own_pct name_own dt_max_h
    *format %11.0f assoc_id
	isid enr_id assoc_id assoc_id_owner role_cd 	//OK, so no need to de-dup
	*g cnt=1
  **to find 34 & 35 pairs (of same owner)

  bys enr_id assoc_id assoc_id_owner: g index=_n
  bys enr_id assoc_id assoc_id_owner: egen cnt_ttl=max(index)
  format %15.0f assoc_id assoc_id_owner
  keep if cnt_ttl>1		//92; 46 pairs of 34 & 35s; review later 
  gsort enr_id role_cd	//34 first, 35 second
  keep assoc_id-role_cd
  format  %50s name* 
save early_steps/hosp/tmp/both34_35, replace	//92 obs;  8 vars
******

   *E. De-dup multiple enr_id 

use "G:\HP\Divisions\HFP\Internal Research Projects\Physicians\PECOS\Ownership data26/db_work26/early_steps/hosp/tmp/both34_35", clear 		//14,728 obs; 89 vars

*Sometimes same enr_id for a hosp-owner pair even though differ effective dates.  
******

  gsort assoc_id assoc_id_owner role_cd -dt_max_h  
  bys 	assoc_id assoc_id_owner dt_max_h role_cd: g index=_n
  order enr_id 	assoc_id ccn assoc_id_owner dt_max_h role_cd index
  keep if index==1		//dropped 3,215; 11,513 obs
  drop index
   
  isid enr_id assoc_id assoc_id_owner   role_cd 	//OK
 
************************

  *F. Finalize hosp-owner file
  
 *For 34-35 pairs, decided to retain 35
  gsort enr_id assoc_id ccn assoc_id_owner -role_cd 
  bys 	enr_id assoc_id assoc_id_owner: g index=_n
  g pair34=0
   replace pair34=1 if index==2					//39 chg;  use index==2 to drop	
  drop index
  isid enr_id assoc_id assoc_id_owner pair34	//OK
  
  bys assoc_id: egen own_pct_ttl=sum(own_pct)		//can include multiple levels of holding companies
  *gsort -own_pct_ttl
  order own_pct_ttl, after (own_pct)
  keep if role_cd==34		//5,807 obs
collapse (sum) own_pct, by (assoc_id)	//3,210 obs
  rename own_pct own34_pct
   gsort -own34_pct
  *format %5.0f own_pct_ttl
  drop effect_dt_oh
save early_steps/hosp/own_2roles_cur_oh, replace	//11,513 obs;  90 var  
****
			*Current owners only, de-dup: sum of 34%
  
use  early_steps/hosp/own_2roles_cur_oh, clear
   keep if inlist(assoc_id,7719899947,5698071173,6103348479)	
   * all 100%
  
  keep if role_cd==34		//3,939 obs
  gsort assoc_id
  order assoc_id own_pct name_prov
assoc_id	own_pct	name_prov
5698071173	100	MCHS HOSPITALS INC
6103348479	100	SAINT MARY OF NAZARETH HOSPITAL - CHICAGO LLC
7719899947	100	BOWLING GREEN-WARREN COUNTY COMMUNITY HOSPITAL CORPORATION


collapse (sum) own_pct, by (assoc_id)	//3,210 obs
gsort -own_pct		//93 own_pct>=200

use early_steps/hosp/own_2roles_cur_oh, clear	//14,728 obs;  89 var 
  bys assoc_id: g index=_n
  keep if index==1		//3,421 obs 
  This, of course, excludes free-standing nonprofit hospitals & govt-owned hosp.  
******

5/4/26; Dutch Rojas, 5/2/26 email
use early_steps/hosp/own_2roles_cur_oh, clear
  keep if strpos(name_own,"MECKLENBURG")
  keep if strpos(name_own,"ATRIUM")
  ccn
340096
340064
340004
340004

******************************************************************************
******************************************************************************

 II. Distribution of sums of ownership shares (table)
 
  
use early_steps/hosp/own_pct34_oh_dedup, clear			//3,944 obs
collapse (sum) own_pct, by (assoc_id name_prov)		//3,210 hosp
  g cat="<=50%"	//non-integers are rounded up
   replace cat="51-90%"   	if own_pct>50
   replace cat="91-100%"  	if own_pct>90
   replace cat="101-150%" 	if own_pct>100
   replace cat="151-250%" 	if own_pct>150
   replace cat=">250%" 	 	if own_pct>250
 
  g cnt=1
   collapse (sum) cnt, by (cat)
   **sort rows in the table
  g rk=1
   replace rk=2 if cat=="51-90%"
   replace rk=3 if cat=="91-100%"
   replace rk=4 if cat=="101-150%"
   replace rk=5 if cat=="151-250%"
   replace rk=6 if cat==">250%"
  sort rk
  drop rk
  paste into table
  
******************************************************************************
******************************************************************************

 III. Typical # of years between oldest and youngest effective dates
 
 use early_steps/hosp/owner_2roles_h26, clear		//18,046 obs; 88 vars
   keep assoc_id name_prov effect_dt_oh
   *keep if inlist(assoc_id,42118887,42121659)
   gsort name_prov -effect_dt_oh
   bys assoc_id: egen early_dt=min(effect_dt_oh) 
   bys assoc_id: egen late_dt =max(effect_dt_oh) 
   g delta=late_dt - early_dt
   g year=delta/365
   *keep if year>50
   summarize year, detail
   
   median difference is 6 years.
   90%ile is 24 years