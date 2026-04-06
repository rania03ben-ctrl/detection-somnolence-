import cv2
import mediapipe as mp

def initialize_face_mesh():
    """Initialise le modèle Face Landmarker de MediaPipe"""
    model_path = 'face_landmarker.task'
    
    base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=1,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False
    )
    face_landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)
    return face_landmarker

def draw_landmarks(image, face_landmarks):
    """Dessine les points du visage sur l'image"""
    mp.tasks.vision.draw_landmarks(
        image,
        face_landmarks,
        connections=mp.tasks.vision.get_connections(mp.tasks.vision.FACE_LANDMARKS)
    )
    mp_drawing_styles = mp.solutions.drawing_styles # Styles de dessin prédéfinis 
    
    mp_drawing.draw_landmarks(
        image=image,
        landmark_list=face_landmarks,
        connections=mp_face_mesh.FACEMESH_TESSELATION, # Connexions entre les points pour former un maillage
        landmark_drawing_spec=None, #   pas de dessin des points individuels
        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style() # Style par défaut pour le maillage
    )
