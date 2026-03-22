---
title: Hadoop ConnectionRefused 및 Path Error 문제 해결 기록
slug: "hadoop-connectionrefused-및-path-error-문제-해결-기록"
category: "data-engineering"
tags: ["connectionrefused", "format", "hadoop", "hdfs", "namenode", "path", "safemode", "troubleshooting"]
status: published
post_type: activity_log
quality_score: 8.0
created_at: "2026-03-02T01:08:09.251948+00:00"
---

# Error

- `ConnectionRefused`
    - hadoop 명령어를 실행하려 했지만 실행되지 않음
        - 원래 상태 그대로 — 실패
            
            ![](/media/posts/imported/dev/BD-General_Untitled_11.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-1_10.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-2_10.png)
            
        - 세션 지우고 새로 만들고 재진행 — 실패
            
            ![](/media/posts/imported/dev/BD-General_Untitled-3_9.png)
            
        - `hadoop namenode -safemode leave`
            - 다른 분들께서는 namenode의 safemode를 해제하였을 때 정상적으로 작동되었다고 함
        - `hadoop namenode -format`
            
            ![](/media/posts/imported/dev/BD-General_Untitled-4_8.png)
            
            - 하지만 safemode를 해제했음에도 불구하고 정상적으로 작동하지 않는 것을 확인함
            - 아이디어
                - 이에 따라, namenode에 불필요한 실행 설정이나 파일이 쌓였다라고 의심을 했고, 이에 따라 네임노드를 밀어버리는게 낫다고 판단하고 포멧을 해주니 정상적으로 작동함
                - [[[Setting]|하둡 파일 시스템 포맷(네임노드)]] 복습 중 세팅 과정 참고
- Path Error
    - 하둡 및 구성 요소들과 리눅스의 HDD 위치는 다르다
    
    ![](/media/posts/imported/dev/BD-General_Untitled-5_8.png)
