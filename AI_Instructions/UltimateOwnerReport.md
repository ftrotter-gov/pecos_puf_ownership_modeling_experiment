Ultimate ownership reportship
============================

When we say "provider organization" we mean clinincal organizations that have one or more clinical facilties with an enrollment in PECOS (Medicare, Medicare Advantage, CHIP and sometimes Medicaid depending on state law).

Facility and address status is complex for these organizations with some clinical locations having multiple campuses and multiple addresses. 

* Report and search capability should show a level of "ultimate owners". So every hospital on a report with a column called "ultimate owners" and there should be more than one row per hospital if there is multiple "ultimate owners". Provider Organizations with multiple ultimate owners, these should listed as "Joint Ventures". Lets have a is_JV column with a yes/no for each row depending on this. 
* A searchble report that lists all of the "ultimate owners". That has multiple count columns: The number of total provider organizations, number of total hospitals, number total hospice etc etc per provider organization type. When we click the number of any of the counts.. we should have new report that shows.. the list of those entities. Limited by organization type or not as per the column count type.
* This report by default should be ordered by the count of all types of organizations... so large ultimate owners at the top of the report. 
* I would like to have a graph view that would show using a force-directed graph of the relationships between owning organizations and provider organizations. I want to have this automatically display the graph two steps away from any given starting entity. (Note: this functionality may require Neo4J or some other graph data engine)
* For each provider organization, I would like to be able to see the hierarchy in an ASCII hierarchy chart that shows the ownership. I would also like the same kind of ASCII chart display in the other direction, where I pick some arbitrary owner and I see the hierarchy of every clinical organization that they work through. 
* Is there a convenient way to use an external public APIs to match up publicly traded companies with the owners. SEC uses simply organization names. 
* Is there a convenient way to link to the IRS 990 for entities that are labeled as non-profit. Could we link into the propublica API for this purpose? 
* 
