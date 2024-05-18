# 프로젝트 개요
**도메인 네임을 주소로 바꿔주는 가상의 DNS name resolution 기반 서비스를 로컬 환경에서 구현한다.**

1. Client 프로세스는 Local DNS server에 query로 도메인 네임을 전달하고 
2. Local DNS server는 자신의 cache에
    - 해당 query의 답이 있으면 바로 reply 하고,
    - 아니면 클라이언트를 대신하여 하나 이상의 다른 DNS server들을 통해 해당 query의 답을 알아낸 후 이를 클라이언트에게 전달한다(recursive query 또는 iterative query). 이 때 query를 처리하면서 얻는 정보를 자신의 cache에 저장하고 이후 들어오는 query에 대해 cache를 최대한 활용한다.

    <img src="./Iterative_query.png" alt="iterative query" width="400" height="250">
    <img src="./Recursive_query.png" alt="recursive query" width="400" height="250">
    
### 조건
1. 각 프로세스 사이의 통신은 모두 UDP를 사용한다.
2. 실제 DNS 서버의 cache엔 여러 형태의 RR이 저장되지만 이 프로젝트에선 CNAME, NS, A만 사용한다.
3. DNS서버 간 UDP통신에서 IP주소는 모두 `localhost:127.0.0.1`을 사용하고 port번호로 프로세스를 식별한다.
4. RR에 저장된 IP 주소는 모두 출력을 위한 가상의 IP주소이다.
5. 모든 DNS서버 cache의 저장공간과 저장된 정보의 유효기간은 무한대라고 가정한다.


### 프로젝트 실행
> ***Ubuntu 18.04.6 LTS 를 사용***

#### 1. init.py 로 cache 초기화
***(생략 가능)*** 모든 DNS서버의 cache를 초기화한다.
```shell
python init.py
```
#### 2. DNS서버 실행
`localDNSserver.py`, `rootDNSserver.py`, `comTLDDNSserver.py`, `companyDNSserver.py`를 실행한다.

```shell
# 각 명령어는 각자 다른 프로세스에서 병렬로 실행
python localDNSserver.py 23002
python rootDNSserver.py 23003
python comTLDDNSserver.py 23004
# config.txt 참고
python companyDNSserver.py <port> <회사이름.txt>
```
명령어 실행 후 recursive 처리 수락 여부와 cache 출력 여부를 설정한다.

#### 3. client.py 실행
client 실행 후 Name resolution할 도메인을 입력한다.
```shell
#예시
python client.py 23001
ipaddr abcdef.com
```
- name resolution 가능한 도메인 목록