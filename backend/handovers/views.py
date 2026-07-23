"""Views for handovers — see PDF HND-1/HND-2."""

from rest_framework import generics

from users.permissions import IsOperator

from .serializers import HandoverSerializer


class HandoverCreateView(generics.CreateAPIView):
    """POST /api/handovers — teslim (delivery) ya da iade (return) kaydı."""

    serializer_class = HandoverSerializer
    permission_classes = [IsOperator]

    def perform_create(self, serializer):
        # created_user: bu teslim/iade işlemini hangi operatörün yaptığının
        # kaydı (BaseModel'in audit alanı burada gerçekten işe yarıyor).
        serializer.save(created_user=self.request.user)