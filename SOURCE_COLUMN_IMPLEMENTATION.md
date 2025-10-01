# Source Column Implementation - Summary

## Overview
Added automatic source extraction from job URLs to populate the `source` column in the `job_applications` table. The source is automatically detected when jobs are synced from SerpAPI Google Jobs or other job boards.

## Changes Made

### 1. Created Source Extractor Utility
**File:** `src/utils/source_extractor.py`

A new utility function `extract_source_from_url(url)` that:
- Extracts the job source/platform from URLs
- Supports 29+ job boards and company career sites
- Returns standardized source names like "LinkedIn", "Indeed", "Glassdoor", etc.

**Supported Sources:**
- Job Boards: LinkedIn, Shine, Glassdoor, Jooble, Instahyre, Indeed, Foundit, Hirist, TimesJobs, Talent.com, Adzuna, Internshala, Naukri, Cutshort, Wellfound, Apna Circle
- Company Career Sites: Barclays, Cognizant, Siemens, Citi, Capgemini, Schneider Electric, BlackRock, Mastercard, United Airlines, Oracle, Mercedes-Benz, Telstra, HPE, UPS, Synechron, BNP Paribas, IBM
- Google Jobs API results
- Generic company websites

### 2. Updated Integration Routes
**File:** `src/integrations_routes.py`

Modified two job insertion points:
1. **`perform_job_sync()` function** - Line ~573
   - Added source extraction before inserting jobs
   - Included `source` column in INSERT query
   - Added `source` parameter to params dict

2. **`perform_job_sync_with_config()` function** - Line ~2022
   - Same modifications as above for custom SerpAPI config syncs

### 3. Updated External Jobs Routes
**File:** `src/external_jobs_routes.py`

Modified four job insertion points:
1. **`search_indeed_jobs()` endpoint**
2. **`search_naukri_jobs()` endpoint**
3. **`search_timesjobs_jobs()` endpoint**
4. **`search_all_indian_jobs()` endpoint**

All now:
- Extract source from URL before insertion
- Include `source` column in INSERT queries
- Pass `source` to database

## How It Works

### When Syncing Jobs from SerpAPI:

```python
# 1. Job comes from Google Jobs API with URL
job = {
    "title": "Software Engineer",
    "company": "ABC Corp",
    "url": "https://in.linkedin.com/jobs/view/12345..."
}

# 2. Source is automatically extracted
job_source = extract_source_from_url(job["url"])  # Returns "LinkedIn"

# 3. Job is saved with source
INSERT INTO job_applications (..., source, ...) 
VALUES (..., 'LinkedIn', ...)
```

### Database Query Result:
```sql
SELECT id, title, company, source FROM job_applications;
```

```
| id  | title              | company    | source    |
|-----|-------------------|------------|-----------|
| 298 | SDE III           | AltiusHub  | LinkedIn  |
| 297 | Full Stack Dev    | Blend      | Shine     |
| 332 | Angular Dev       | Pyramid    | Glassdoor |
```

## Benefits

✅ **Automatic Source Tracking** - No manual intervention needed  
✅ **Accurate Source Attribution** - Extracted directly from job URLs  
✅ **Job Discovery Filtering** - Users can filter jobs by source  
✅ **Analytics** - Track which sources provide the best jobs  
✅ **Transparency** - Users know where each job came from  

## Frontend Integration

The frontend can now display the source in job cards:

```javascript
// Example job card display
<JobCard>
  <JobTitle>{job.title}</JobTitle>
  <Company>{job.company}</Company>
  <Source>
    <Badge>{job.source}</Badge> {/* Shows "LinkedIn", "Indeed", etc. */}
  </Source>
</JobCard>
```

## Testing

To verify the implementation works:

1. **Sync jobs from Google Jobs API:**
   ```
   POST /api/integrations/job-sources/googlejobs/sync
   ```

2. **Check the database:**
   ```sql
   SELECT source, COUNT(*) as count 
   FROM job_applications 
   WHERE source IS NOT NULL 
   GROUP BY source 
   ORDER BY count DESC;
   ```

3. **Verify sources are populated:**
   - All new jobs should have a `source` value
   - Source should match the URL domain
   - No jobs should have NULL or 'Unknown' source

## Future Enhancements

- Add source filtering in Job Discovery API
- Create source analytics dashboard
- Add source preference settings for users
- Implement source-based job ranking

## Rollback Plan

If needed, the source column can be made nullable:
```sql
ALTER TABLE job_applications ALTER COLUMN source DROP NOT NULL;
```

Then remove source extraction from the code and redeploy.
