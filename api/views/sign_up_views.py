from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.request import Request



from api.serializers.sign_up_serializer import SignUpSerializer

class SignUpView(generics.GenericAPIView) : 

    permission_classes = ()
    serializer_class = SignUpSerializer
    
    def post(self, request:Request):
        data = request.data

        serializer=self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.save()

            response ={
                "message": "El usuario se ha creado con éxito",
                "data": serializer.data
            }

            return Response(data=response, status=status.HTTP_201_CREATED)
        
        return Response(data=serializer.data, status=status.HTTP_400_BAD_REQUEST)