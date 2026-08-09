from fastapi.testclient import TestClient
from main import app, repository, engine

client = TestClient(app)

def test_01_new_interview_session():
    """Test 1: New interview session creation."""
    res = client.post("/api/interview", json={"candidate": "CAND-001", "personality": "Senior Engineer"})
    assert res.status_code == 200
    data = res.json()
    assert "sessionId" in data or "session_id" in data
    assert data["done"] == False
    assert len(data["reply"]) > 0

def test_02_second_conversation_turn():
    """Test 2: Second conversation turn."""
    start_res = client.post("/api/interview", json={"candidate": "CAND-001"})
    sid = start_res.json()["sessionId"]

    turn_res = client.post("/api/interview", json={
        "sessionId": sid,
        "message": "Sentence Transformers output dense embeddings like 384 dimensions, compared to OpenAI 1536 dims."
    })
    assert turn_res.status_code == 200
    turn_data = turn_res.json()
    assert turn_data["done"] == False
    assert len(turn_data["reply"]) > 0

def test_03_existing_session_retains_state():
    """Test 3: Existing session retains state across requests."""
    start_res = client.post("/api/interview", json={"candidate": "CAND-002"})
    sid = start_res.json()["sessionId"]

    # Turn 1
    client.post("/api/interview", json={"sessionId": sid, "message": "First response detailing vector DB setup."})
    
    # Check session state in backend
    get_res = client.get(f"/api/interview/session/{sid}")
    assert get_res.status_code == 200
    sess_data = get_res.json()
    assert sess_data["candidate"]["member"]["id"] == "CAND-002"
    assert len(sess_data["turns"]) == 2

def test_04_minimum_8_questions():
    """Test 4: Enforce minimum 8 questions before completion."""
    start_res = client.post("/api/interview", json={"candidate": "CAND-003"})
    sid = start_res.json()["sessionId"]

    curr_data = start_res.json()
    turn_count = 1
    
    answers = [
        "In Day 7 we created dense embeddings with SentenceTransformers.",
        "In Day 8 we indexed vectors in ChromaDB with cosine distance.",
        "In Day 10 we built hybrid retrieval router between SQL and vector search.",
        "In Day 11 we built RAG system prompt to prevent hallucination.",
        "In Day 12 we tested zero-shot and chain-of-thought prompt engineering.",
        "In Day 13 we implemented OpenAI function calling with Pydantic validation.",
        "In Day 21 we created LangChain ReAct reasoning agents with tools.",
        "In Day 22 we used CrewAI and LangGraph for multi-agent supervisor routing.",
        "In Day 23 we exposed tools via Model Context Protocol (MCP) server."
    ]

    for ans in answers:
        if curr_data.get("done"):
            break
        chat_res = client.post("/api/interview", json={"sessionId": sid, "message": ans})
        assert chat_res.status_code == 200
        curr_data = chat_res.json()
        turn_count += 1

    assert turn_count >= 8

def test_05_minimum_4_curriculum_days():
    """Test 5: Minimum 4 curriculum days assessed."""
    start_res = client.post("/api/interview", json={"candidate": "CAND-001"})
    sid = start_res.json()["sessionId"]

    answers = [
        "Sentence Transformers 384 dim vectors.",
        "ChromaDB local vector DB.",
        "Query router for hybrid retrieval.",
        "RAG prompt engineering with CoT.",
        "FastAPI backend /chat endpoint.",
        "Multi-agent supervisor routing.",
        "Model Context Protocol MCP servers.",
        "Docker Kubernetes container deployment."
    ]

    curr_data = start_res.json()
    for ans in answers:
        if curr_data.get("done"):
            break
        chat_res = client.post("/api/interview", json={"sessionId": sid, "message": ans})
        curr_data = chat_res.json()

    if not curr_data.get("done"):
        finish_res = client.post("/api/interview/finish", json={"sessionId": sid})
        curr_data = finish_res.json()

    assert curr_data["done"] == True
    assert len(curr_data["feedback"]["covered_days"]) >= 4

def test_06_skipped_topic_not_treated_as_completed():
    """Test 6: Skipped topic is not treated as completed."""
    # CAND-001 skipped Day 29 ("Monitoring, Logging & Observability")
    start_res = client.post("/api/interview", json={"candidate": "CAND-001"})
    sid = start_res.json()["sessionId"]

    sess_res = client.get(f"/api/interview/session/{sid}")
    sess_data = sess_res.json()
    
    assert 29 not in sess_data["covered_days"]

def test_07_final_response_feedback_contract():
    """Test 7: Final response contains done=true and required feedback fields (summary, strengths, gaps, next)."""
    start_res = client.post("/api/interview", json={"candidate": "CAND-001"})
    sid = start_res.json()["sessionId"]

    finish_res = client.post("/api/interview/finish", json={"sessionId": sid})
    assert finish_res.status_code == 200
    data = finish_res.json()

    assert data["done"] == True
    assert "feedback" in data
    fb = data["feedback"]
    assert "summary" in fb and isinstance(fb["summary"], str)
    assert "strengths" in fb and isinstance(fb["strengths"], list)
    assert "gaps" in fb and isinstance(fb["gaps"], list)
    assert "next" in fb and isinstance(fb["next"], list)

def test_08_unknown_session_id_handling():
    """Test 8: Unknown sessionId returns 404 HTTP error."""
    res = client.post("/api/interview", json={"sessionId": "non_existent_session_9999", "message": "Hello"})
    assert res.status_code == 404

def test_09_invalid_request_handling():
    """Test 9: Invalid request payload returns 400 HTTP error."""
    res = client.post("/api/interview/chat", json={"session_id": ""})
    assert res.status_code == 400

def test_10_candidate_personalization():
    """Test 10: Candidate personalization matches completed missions."""
    res1 = client.post("/api/interview", json={"candidate": "CAND-001"})
    res2 = client.post("/api/interview", json={"candidate": "CAND-005"})
    
    data1 = res1.json()
    data2 = res2.json()

    assert "Sarah" in data1["reply"]
    assert "Michael" in data2["reply"]
