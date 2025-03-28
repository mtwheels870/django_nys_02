from django.shortcuts import get_object_or_404

class SurveyUtil:
    @staticmethod
    def copy_geography(survey_id, parent_survey_id):
        from .models import (IpRangeSurvey, IpSurveyCounty, IpSurveyTract)

        print(f"SurveyUtil.copy_geography(), survey_id = {survey_id}, parent_survey_id = {parent_survey_id}")
        survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
        parent_survey = get_object_or_404(IpRangeSurvey, pk=parent_survey_id)

        state_set = parent_survey.ipsurveystate_set.all()
        for parent_state in state_set:
            new_survey_state = IpSurveyState(survey=survey,us_state=parent_state.us_state)
            new_survey_state.save()

        county_set = parent_survey.ipsurveycounty_set.all()
        for parent_county in county_set:
            new_survey_county = IpSurveyCounty(survey=survery, county=parent_county.county)
            new_survey_county.save()

        tract_set = parent_survey.ipsurveytract_set.all()
        for parent_tract in tract_set:
            new_survey_tract = IpSurveyTract(survey=survey,tract=parent_tract.tract)
            new_survey_tract.save()

    @staticmethod
    def _delete_surveys(survey_ids):
        from .models import (IpRangeSurvey, IpSurveyCounty, IpSurveyTract)

        print(f"PSM._delete_surveys(), surveys: {survey_ids}")
        for survey_id in survey_ids:
            print(f"   deleting survey = {survey_id}")
            survey = get_object_or_404(IpRangeSurvey, pk=survey_id)

            iprange_set = survey.iprangeping_set.all()
            for range1 in iprange_set:
                range1.delete()

            tract_set = survey.ipsurveytract_set.all()
            for tract in tract_set:
                tract.delete()

            county_set = survey.ipsurveycounty_set.all()
            for county in county_set:
                county.delete()

            state_set = survey.ipsurveystate_set.all()
            for state in state_set:
                state.delete()

            num_tracts = tract_set.count()
            num_counties = county_set.count()
            num_states = state_set.count()
            print(f"      deleted s/c/t: {num_states}/{num_counties}/{num_tracts}")
            survey.delete()
        return True

    @staticmethod
    def link_file_string(survey_id, parent_survey_id):
        from .ping import PingSurveyManager

        return PingSurveyManager.link_survey(survey_id, int(parent_survey_id))
