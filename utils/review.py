"""复习相关工具数式"""

from datetime import date, timedelta

all = ['adjust_plan', 'get_next_review_date']


FEEDBACK_MAP = {
    0:0.5,
    1:0.7,
    2:1,
    3:1.2
}
FEEDBACK_MUTI_FACTOR = 1
FEEDBAKC_AMEND_FACTOR = 1
MAX_INTERVAL = 60
MIN_INTERVAL = 1

def adjust_and_get_next(plan:str,feedback,last_feedback, stage):
    feedback = feedback or 2
    last_feedback = last_feedback or 2

    feedback = FEEDBACK_MAP.get(int(feedback),1)
    last_feedback = FEEDBACK_MAP.get(int(last_feedback),1)
    plan_list = list(map(lambda x: float(x), plan.split(',')))
    plan_list_len = len(plan_list)
    if stage>=plan_list_len:
        stage = plan_list_len-1
    elif stage<0:
        stage = 0
    
    interval = plan_list[stage]
    new_interval = interval*FEEDBACK_MUTI_FACTOR*(feedback+FEEDBAKC_AMEND_FACTOR*(feedback-last_feedback))
    if new_interval<MIN_INTERVAL:
        new_interval = MIN_INTERVAL
    if new_interval>MAX_INTERVAL:
        new_interval = MAX_INTERVAL
    plan_list[stage] = new_interval
    for i in range(len(plan_list)):
        cur = plan_list[i]
        if i>=stage:
            new_interval = cur*FEEDBACK_MUTI_FACTOR*(feedback+FEEDBAKC_AMEND_FACTOR*(feedback-last_feedback))
            if new_interval<MIN_INTERVAL:
                new_interval = MIN_INTERVAL
            if new_interval>MAX_INTERVAL:
                new_interval = MAX_INTERVAL
            cur = new_interval
        plan_list[i] = '{:.2f}'.format(cur) # type: ignore
    new_plan = ','.join(plan_list) # type: ignore

    new_stage = stage+1 if stage< plan_list_len-1 else stage

    next_review_date = date.today()+timedelta(days=int(float((plan_list[new_stage]))))

    return new_plan,new_stage,next_review_date


