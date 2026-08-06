const { protect, admin } = require('../middlewares/auth');
const jwt = require('jsonwebtoken');
const User = require('../models/User');

jest.mock('jsonwebtoken');
jest.mock('../models/User');

describe('Auth Middleware', () => {
  let mockRequest;
  let mockResponse;
  let nextFunction;

  beforeEach(() => {
    mockRequest = {
      headers: {},
    };
    mockResponse = {
      statusCode: 200,
      status: jest.fn().mockImplementation(function (code) {
        this.statusCode = code;
        return this;
      }),
      json: jest.fn(),
    };
    nextFunction = jest.fn();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    console.error.mockRestore();
    jest.clearAllMocks();
  });

  describe('protect middleware', () => {
    test('should allow authorized user with valid token', async () => {
      mockRequest.headers.authorization = 'Bearer validtoken123';
      jwt.verify.mockReturnValue({ id: 'user123' });
      
      const mockUser = { _id: 'user123', name: 'John Doe', role: 'user' };
      User.findById.mockReturnValue({
        select: jest.fn().mockResolvedValue(mockUser),
      });

      await protect(mockRequest, mockResponse, nextFunction);

      expect(jwt.verify).toHaveBeenCalledWith('validtoken123', expect.any(String));
      expect(User.findById).toHaveBeenCalledWith('user123');
      expect(mockRequest.user).toEqual(mockUser);
      expect(nextFunction).toHaveBeenCalled();
      expect(mockResponse.status).not.toHaveBeenCalled();
    });

    test('should return 401 if authorization header is missing', async () => {
      await protect(mockRequest, mockResponse, nextFunction);

      expect(mockResponse.status).toHaveBeenCalledWith(401);
      expect(mockResponse.json).toHaveBeenCalledWith({
        success: false,
        message: 'Not authorized, no token provided',
      });
      expect(nextFunction).not.toHaveBeenCalled();
    });

    test('should return 401 if token is invalid/fails verification', async () => {
      mockRequest.headers.authorization = 'Bearer invalidtoken123';
      jwt.verify.mockImplementation(() => {
        throw new Error('Invalid token');
      });

      await protect(mockRequest, mockResponse, nextFunction);

      expect(mockResponse.status).toHaveBeenCalledWith(401);
      expect(mockResponse.json).toHaveBeenCalledWith({
        success: false,
        message: 'Not authorized, token failed',
      });
      expect(nextFunction).not.toHaveBeenCalled();
    });

    test('should return 401 if user is not found in database', async () => {
      mockRequest.headers.authorization = 'Bearer validtoken123';
      jwt.verify.mockReturnValue({ id: 'nonexistentuser' });
      User.findById.mockReturnValue({
        select: jest.fn().mockResolvedValue(null),
      });

      await protect(mockRequest, mockResponse, nextFunction);

      expect(mockResponse.status).toHaveBeenCalledWith(401);
      expect(mockResponse.json).toHaveBeenCalledWith({
        success: false,
        message: 'Not authorized, user not found',
      });
      expect(nextFunction).not.toHaveBeenCalled();
    });
  });

  describe('admin middleware', () => {
    test('should allow access if user is admin', () => {
      mockRequest.user = { role: 'admin' };

      admin(mockRequest, mockResponse, nextFunction);

      expect(nextFunction).toHaveBeenCalled();
      expect(mockResponse.status).not.toHaveBeenCalled();
    });

    test('should return 403 if user is not admin', () => {
      mockRequest.user = { role: 'user' };

      admin(mockRequest, mockResponse, nextFunction);

      expect(mockResponse.status).toHaveBeenCalledWith(403);
      expect(mockResponse.json).toHaveBeenCalledWith({
        success: false,
        message: 'Not authorized as an admin',
      });
      expect(nextFunction).not.toHaveBeenCalled();
    });
  });
});
