# In app.py, check the handle_voice_input function
def handle_voice_input(client: VoiceAIClient):
    UI.render_voice_banner()
    audio_msg = st.audio_input(
        "Record your message",
        key=f"voice_{st.session_state.audio_key}",
        label_visibility="collapsed"
    )

    if audio_msg:
        # DEBUG: Check if audio was recorded
        st.write(f"Audio recorded: {audio_msg.size} bytes")  # Add this debug line
        
        col_send, col_cancel = st.columns([1, 3])
        with col_send:
            send = st.button("Send Voice", use_container_width=True, type="primary", key="send_voice_btn")
        with col_cancel:
            cancel = st.button("Cancel", use_container_width=True, key="cancel_voice_btn")

        if cancel:
            st.session_state.audio_key += 1
            st.session_state.voice_recorded = False
            st.rerun()

        if send:
            with st.spinner("🎤 Transcribing and generating response..."):
                try:
                    # CRITICAL: Get the audio bytes correctly
                    audio_bytes = audio_msg.getvalue()  # This should work
                    
                    # DEBUG: Verify bytes
                    st.write(f"Sending {len(audio_bytes)} bytes to API")  # Add debug
                    
                    response_audio, response_text, error = client.send_voice(
                        audio_bytes,
                        st.session_state.user_id
                    )
                    
                    # DEBUG: Check response
                    st.write(f"Response: error={error}, has_audio={response_audio is not None}")
                    
                    if error:
                        st.error(f"❌ {error}")
                        st.session_state.api_error_count += 1
                        return

                    if response_audio or response_text:
                        st.session_state.api_error_count = 0
                        assistant_msg = ChatMessage(
                            role="assistant",
                            content=response_text or "Voice response generated",
                            audio=response_audio
                        )
                        SessionState.add_message(assistant_msg)
                        st.session_state.audio_key += 1
                        st.session_state.voice_recorded = False
                        st.rerun()
                    else:
                        st.warning("⚠️ No response received from the server.")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.api_error_count += 1
